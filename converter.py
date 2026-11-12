"""
Invoice & Sale Certificate Converter Module
Converts Shanti Motors Tax Invoices & Sale Certificates into Annapurna Motors format.
Supports dynamic Hypothecation bank selection and Date replacement.
"""

import os
import re
import fitz  # PyMuPDF

# Annapurna Motors Dealership Configurations
ANNAPURNA_INVOICE_CONFIG = {
    "dealer_name": "ANNAPURNA MOTORS",
    "address_line1": "Khasra 193/1  Ward 15 Alirajpur Road",
    "address_line2": "KUKSHI DHAR MADHYA PRADESH 454331 State Code: 23 Contact #     9755820013",
    "dealer_auth": "Authorized Dealer: Hero MotoCorp Ltd.",
    "gstin_pan": "GSTIN #: 23AFTPG6974R1ZE PAN# AFTPG6974R",
    "footer_signatory": "For ANNAPURNA MOTORS",
}

ANNAPURNA_SC_CONFIG = {
    "dealer_name": "ANNAPURNA MOTORS",
    "address_line1": "Khasra 193/1  Ward 15 Alirajpur Road",
    "address_line2": "KUKSHI DHAR MADHYA PRADESH 454331 Contact# 9755820013",
    "dealer_auth": "Authorized Dealer: Hero MotoCorp Ltd.",
    "footer_signatory": "For ANNAPURNA MOTORS",
}

# Supported Hypothecation Banks
HYPOTHECATION_OPTIONS = [
    "KEEP_ORIGINAL",
    "HERO FINCORP LTD",
    "TATA CAPITAL LTD",
    "AASTHA SAKH SAHKARITA",
    "BLANK"
]


def detect_document_type(doc: fitz.Document) -> str:
    """Detect whether the document is a Sale Certificate or Tax Invoice."""
    first_page_text = doc[0].get_text()
    if "SALE CERTIFICATE" in first_page_text or "Form No .21" in first_page_text:
        return "sale_certificate"
    return "invoice"


def update_hypothecation_invoice(page: fitz.Page, hypothecation: str) -> bool:
    """Update or blank out hypothecation on a Tax Invoice page."""
    if not hypothecation or hypothecation == "KEEP_ORIGINAL":
        return False

    hits = page.search_for("Hypothecation with")
    if not hits:
        return False
    h = hits[0]

    # Target the value area to the right of 'Hypothecation with'
    val_rect = fitz.Rect(125, h.y0 - 2, 350, h.y1 + 2)
    page.add_redact_annot(val_rect, fill=(1, 1, 1))
    page.apply_redactions()

    if hypothecation != "BLANK":
        page.insert_text(
            (132.30, h.y1 - 0.5),
            hypothecation.strip(),
            fontsize=9.0,
            fontname="helv",
            color=(0, 0, 0)
        )
    return True


def update_hypothecation_sale_certificate(page: fitz.Page, hypothecation: str) -> bool:
    """Update or blank out hypothecation on a Sale Certificate page."""
    if not hypothecation or hypothecation == "KEEP_ORIGINAL":
        return False

    hits = page.search_for("hypothecation with")
    if not hits:
        return False
    h = hits[0]

    # Value in Sale Certificate starts around x = 310
    val_rect = fitz.Rect(310, h.y0 - 2, 530, h.y1 + 2)
    page.add_redact_annot(val_rect, fill=(1, 1, 1))
    page.apply_redactions()

    if hypothecation != "BLANK":
        page.insert_text(
            (326.25, h.y1 - 0.5),
            hypothecation.strip(),
            fontsize=9.0,
            fontname="helv",
            color=(0, 0, 0)
        )
    return True


def update_date_invoice(page: fitz.Page, new_date_str: str) -> bool:
    """Update Date on Tax Invoice while preserving original time if present."""
    if not new_date_str or not new_date_str.strip():
        return False

    date_hits = [h for h in page.search_for("Date") if 200 < h.y0 < 250 and h.x0 > 380]
    if not date_hits:
        return False
    dh = date_hits[0]

    val_rect = fitz.Rect(dh.x1 + 5, dh.y0 - 2, 580, dh.y1 + 2)
    old_text = page.get_text("text", clip=val_rect).strip()
    time_match = re.search(r"\d{1,2}:\d{2}(?::\d{2})?", old_text)
    time_part = f" {time_match.group(0)}" if time_match else ""

    page.add_redact_annot(val_rect, fill=(1, 1, 1))
    page.apply_redactions()

    if re.search(r"\d{1,2}:\d{2}", new_date_str):
        final_date = new_date_str.strip()
    else:
        final_date = f"{new_date_str.strip()}{time_part}"

    page.insert_text(
        (479.8, dh.y1 - 0.5),
        final_date,
        fontsize=9.0,
        fontname="helv",
        color=(0, 0, 0)
    )
    return True


def update_date_sale_certificate(page: fitz.Page, new_date_str: str) -> bool:
    """Update Date at top-right and in the body paragraph of Sale Certificate."""
    if not new_date_str or not new_date_str.strip():
        return False

    clean_match = re.search(r"\d{2}/\d{2}/\d{4}", new_date_str)
    date_only = clean_match.group(0) if clean_match else new_date_str.strip()

    # 1. Top right date
    date_hits = [h for h in page.search_for("Date") if 100 < h.y0 < 140 and h.x0 > 450]
    old_date = None
    if date_hits:
        dh = date_hits[0]
        val_rect = fitz.Rect(dh.x1 + 5, dh.y0 - 2, 580, dh.y1 + 2)
        old_text = page.get_text("text", clip=val_rect).strip()
        m = re.search(r"\d{2}/\d{2}/\d{4}", old_text)
        if m:
            old_date = m.group(0)

        page.add_redact_annot(val_rect, fill=(1, 1, 1))
        page.apply_redactions()
        page.insert_text(
            (512.1, dh.y1 - 0.5),
            f"  {date_only}",
            fontsize=9.0,
            fontname="helv",
            color=(0, 0, 0)
        )

    # 2. Date in body paragraph (e.g. 'delivered by us on date 11/11/2026 with')
    if old_date:
        for hit in page.search_for(old_date):
            if 150 < hit.y0 < 250:
                page.add_redact_annot(
                    fitz.Rect(hit.x0 - 1, hit.y0 - 1, hit.x1 + 1, hit.y1 + 1),
                    fill=(1, 1, 1)
                )
                page.apply_redactions()
                page.insert_text(
                    (hit.x0, hit.y1 - 0.5),
                    date_only,
                    fontsize=9.0,
                    fontname="helv",
                    color=(0, 0, 0)
                )
    return True


def convert_invoice(doc: fitz.Document, hypothecation: str = None, new_date: str = None) -> dict:
    """Convert a Shanti Motors Tax Invoice into Annapurna Motors format."""
    cfg = ANNAPURNA_INVOICE_CONFIG
    headers_replaced = 0
    footers_replaced = 0

    for page in doc:
        # 1. Replace Header
        shanti_hits = page.search_for("SHANTI MOTORS")
        gstin_hits = page.search_for("23AQMPP0120E1ZE")
        header_hit = any(h.y0 < 200 for h in shanti_hits)

        if header_hit or (gstin_hits and gstin_hits[0].y0 < 200):
            header_rect = fitz.Rect(26.0, 106.0, 440.0, 170.0)
            page.add_redact_annot(header_rect, fill=(1, 1, 1))
            page.apply_redactions()

            page.insert_text((28.35, 120.5), cfg["dealer_name"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
            page.insert_text((28.35, 131.0), cfg["address_line1"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
            page.insert_text((28.35, 142.0), cfg["address_line2"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
            page.insert_text((28.35, 153.0), cfg["dealer_auth"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
            page.insert_text((28.35, 164.0), cfg["gstin_pan"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
            headers_replaced += 1

        # 2. Update Hypothecation if requested
        if hypothecation:
            update_hypothecation_invoice(page, hypothecation)

        # 3. Update Date if requested
        if new_date:
            update_date_invoice(page, new_date)

        # 4. Replace Footer Signatory
        footer_hits = [h for h in page.search_for("SHANTI MOTORS") if h.y0 > 200]
        if not footer_hits:
            footer_hits = [h for h in page.search_for("M/S.SHANTI MOTORS") if h.y0 > 200]

        for rect in footer_hits:
            expanded_rect = fitz.Rect(rect.x0 - 55, rect.y0 - 2, rect.x1 + 30, rect.y1 + 2)
            page.add_redact_annot(expanded_rect, fill=(1, 1, 1))
            page.apply_redactions()

            footer_text = cfg["footer_signatory"]
            text_len = fitz.get_text_length(footer_text, fontname="helv", fontsize=9.0)
            target_x = max(28.35, 577.05 - text_len)
            page.insert_text((target_x, rect.y1 - 1.5), footer_text, fontsize=9.0, fontname="helv", color=(0, 0, 0))
            footers_replaced += 1

    return {
        "doc_type": "invoice",
        "headers_replaced": headers_replaced,
        "footers_replaced": footers_replaced,
    }


def convert_sale_certificate(doc: fitz.Document, hypothecation: str = None, new_date: str = None) -> dict:
    """Convert a Shanti Motors Sale Certificate into Annapurna Motors format."""
    cfg = ANNAPURNA_SC_CONFIG
    headers_replaced = 0
    footers_replaced = 0

    for page in doc:
        # 1. Header Block on Sale Certificate (x: ~54 to 440, y: ~22 to 75)
        shanti_hits = [h for h in page.search_for("Shanti Motors") if h.y0 < 100]
        if not shanti_hits:
            shanti_hits = [h for h in page.search_for("SHANTI MOTORS") if h.y0 < 100]

        if shanti_hits:
            page.add_redact_annot(fitz.Rect(54.0, 22.0, 440.0, 75.0), fill=(1, 1, 1))
            page.apply_redactions()

            page.insert_text((56.7, 35.0), cfg["dealer_name"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
            page.insert_text((56.7, 46.0), cfg["address_line1"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
            page.insert_text((56.7, 57.0), cfg["address_line2"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
            page.insert_text((56.7, 68.0), cfg["dealer_auth"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
            headers_replaced += 1

        # 2. Update Hypothecation if requested
        if hypothecation:
            update_hypothecation_sale_certificate(page, hypothecation)

        # 3. Update Date if requested
        if new_date:
            update_date_sale_certificate(page, new_date)

        # 4. Replace Footer Signatory ('For M/s.Shanti Motors')
        footer_hits = [h for h in page.search_for("Shanti Motors") if h.y0 > 200]
        if not footer_hits:
            footer_hits = [h for h in page.search_for("SHANTI MOTORS") if h.y0 > 200]

        for rect in footer_hits:
            expanded_rect = fitz.Rect(rect.x0 - 55, rect.y0 - 2, rect.x1 + 30, rect.y1 + 2)
            page.add_redact_annot(expanded_rect, fill=(1, 1, 1))
            page.apply_redactions()

            footer_text = cfg["footer_signatory"]
            text_len = fitz.get_text_length(footer_text, fontname="helv", fontsize=9.0)
            target_x = max(56.7, 570.0 - text_len)
            page.insert_text((target_x, 605.0), footer_text, fontsize=9.0, fontname="helv", color=(0, 0, 0))
            footers_replaced += 1

    return {
        "doc_type": "sale_certificate",
        "headers_replaced": headers_replaced,
        "footers_replaced": footers_replaced,
    }


def convert_document(input_path: str, output_path: str, hypothecation: str = None, new_date: str = None) -> dict:
    """
    Main conversion entry point.
    Automatically detects whether the document is a Tax Invoice or Sale Certificate,
    then executes high-precision redaction, header replacement, footer alignment,
    hypothecation bank updating, and date changes.
    """
    doc = fitz.open(input_path)
    total_pages = len(doc)
    doc_type = detect_document_type(doc)

    if doc_type == "sale_certificate":
        stats = convert_sale_certificate(doc, hypothecation=hypothecation, new_date=new_date)
    else:
        stats = convert_invoice(doc, hypothecation=hypothecation, new_date=new_date)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    stats["pages_processed"] = total_pages
    stats["status"] = "success"
    return stats


# Aliases for backward compatibility
convert_shanti_to_annapurna = convert_document


def batch_convert(input_dir: str, output_dir: str, hypothecation: str = None, new_date: str = None, progress_callback=None) -> list:
    """Batch convert all PDF invoices and sale certificates in a directory."""
    os.makedirs(output_dir, exist_ok=True)
    results = []
    files = [p for p in sorted(os.listdir(input_dir)) if p.lower().endswith('.pdf')]
    total = len(files)

    for idx, filename in enumerate(files):
        in_file = os.path.join(input_dir, filename)
        base_stem, ext = os.path.splitext(filename)
        out_file = os.path.join(output_dir, f"{base_stem}_smn{ext}")

        try:
            res = convert_document(in_file, out_file, hypothecation=hypothecation, new_date=new_date)
            res["filename"] = filename
            res["output_path"] = out_file
            results.append(res)
        except Exception as e:
            results.append({
                "filename": filename,
                "output_path": out_file,
                "status": "error",
                "error": str(e)
            })

        if progress_callback:
            progress_callback(idx + 1, total, filename)

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hero MotoCorp Dealership Document Converter")
    parser.add_argument("--input", "-i", required=True, help="Input PDF file or folder")
    parser.add_argument("--output", "-o", required=True, help="Output PDF file or folder")
    parser.add_argument("--hypo", choices=HYPOTHECATION_OPTIONS, default="KEEP_ORIGINAL", help="Hypothecation bank")
    parser.add_argument("--date", help="Optional new date (DD/MM/YYYY)")

    args = parser.parse_args()

    if os.path.isdir(args.input):
        print(f"Batch converting: {args.input} -> {args.output}")
        out = batch_convert(args.input, args.output, hypothecation=args.hypo, new_date=args.date)
        for item in out:
            print(f"[{item['status'].upper()}] {item['filename']} -> {item.get('output_path', '')}")
    else:
        res = convert_document(args.input, args.output, hypothecation=args.hypo, new_date=args.date)
        print("Result:", res)
