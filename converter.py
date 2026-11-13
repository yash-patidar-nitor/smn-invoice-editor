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

STAMP_FILE_NAME = "stamp.png"


def get_stamp_path() -> str:
    """Find the path to the Annapurna Motors official stamp image."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, STAMP_FILE_NAME),
        os.path.join(base_dir, "assets", STAMP_FILE_NAME),
        os.path.join(os.path.dirname(base_dir), "annapurna_stamp_perfect.png"),
        os.path.join(base_dir, "annapurna_stamp_perfect.png")
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def affix_dealer_stamp_invoice(page: fitz.Page, stamp_path: str = None) -> bool:
    """Affix authentic Annapurna Motors circular rubber stamp and signature onto Tax Invoice."""
    path = stamp_path or get_stamp_path()
    if not path or not os.path.exists(path):
        return False
    # Tax Invoice: centered over Authorized Signatory line
    rect = fitz.Rect(438, 680, 524, 766)
    page.insert_image(rect, filename=path, keep_proportion=True)
    return True


def affix_dealer_stamp_sale_certificate(page: fitz.Page, stamp_path: str = None) -> bool:
    """Affix authentic Annapurna Motors circular rubber stamp and signature onto Form 21 Sale Certificate."""
    path = stamp_path or get_stamp_path()
    if not path or not os.path.exists(path):
        return False
    # Sale Certificate: positioned between For ANNAPURNA MOTORS and Authorized Signatory
    rect = fitz.Rect(438, 614, 522, 700)
    page.insert_image(rect, filename=path, keep_proportion=True)
    return True



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

    # Target the value area strictly between y=338.0 and 348.8 so Mobile # at y<=337.5 is NEVER truncated
    val_rect = fitz.Rect(125.0, 338.0, 360.0, 348.8)
    page.add_redact_annot(val_rect, fill=(1, 1, 1))
    page.apply_redactions()

    if hypothecation != "BLANK":
        page.insert_text(
            (132.30, 346.64),
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

    # Value in Sale Certificate starts around x = 320, strictly between y=357.0 and 369.0
    val_rect = fitz.Rect(320.0, 357.0, 530.0, 369.0)
    page.add_redact_annot(val_rect, fill=(1, 1, 1))
    page.apply_redactions()

    if hypothecation != "BLANK":
        page.insert_text(
            (326.25, 366.27),
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

    # Strictly between y=223.5 and 234.5 so Invoice # at y<=223.0 is NEVER truncated
    val_rect = fitz.Rect(478.0, 223.5, 580.0, 234.5)
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
        (479.8, 232.17),
        f" {final_date.lstrip()}",
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

    # 1. Top right date: strictly y=121.0 to 133.0
    val_rect = fitz.Rect(510.0, 121.0, 580.0, 133.0)
    old_text = page.get_text("text", clip=val_rect).strip()
    old_date = None
    m = re.search(r"\d{2}/\d{2}/\d{4}", old_text)
    if m:
        old_date = m.group(0)

    page.add_redact_annot(val_rect, fill=(1, 1, 1))
    page.apply_redactions()
    page.insert_text(
        (512.1, 130.19),
        f"  {date_only}",
        fontsize=9.0,
        fontname="helv",
        color=(0, 0, 0)
    )

    # 2. Date in body paragraph (e.g. 'delivered by us on date 11/11/2026 with')
    # Strictly between y=190.0 and 200.0, x=64.0 and 115.0
    body_date_rect = fitz.Rect(64.0, 190.0, 115.0, 200.0)
    page.add_redact_annot(body_date_rect, fill=(1, 1, 1))
    page.apply_redactions()
    page.insert_text(
        (65.7, 197.83),
        date_only,
        fontsize=9.0,
        fontname="helv",
        color=(0, 0, 0)
    )
    return True


def convert_invoice(doc: fitz.Document, hypothecation: str = None, new_date: str = None, affix_stamp: bool = True) -> dict:
    """Convert a Shanti Motors Tax Invoice into Annapurna Motors format. Strictly touches Page 1 only."""
    cfg = ANNAPURNA_INVOICE_CONFIG
    headers_replaced = 0
    footers_replaced = 0

    if len(doc) == 0:
        return {"doc_type": "invoice", "headers_replaced": 0, "footers_replaced": 0, "stamp_affixed": False}

    # Invoice content is strictly on Page 0 (Page 1 is Terms & Conditions which must stay untouched)
    page = doc[0]

    # 1. Replace Header on Page 0
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

    # 2. Update Hypothecation on Page 0
    if hypothecation:
        update_hypothecation_invoice(page, hypothecation)

    # 3. Update Date on Page 0
    if new_date:
        update_date_invoice(page, new_date)

    # 4. Replace Footer Signatory on Page 0
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

    # 5. Affix Authentic Stamp & Signature
    stamp_affixed = False
    if affix_stamp:
        stamp_affixed = affix_dealer_stamp_invoice(page)

    return {
        "doc_type": "invoice",
        "headers_replaced": headers_replaced,
        "footers_replaced": footers_replaced,
        "stamp_affixed": stamp_affixed
    }


def convert_sale_certificate(doc: fitz.Document, hypothecation: str = None, new_date: str = None, affix_stamp: bool = True) -> dict:
    """Convert a Shanti Motors Sale Certificate into Annapurna Motors format."""
    cfg = ANNAPURNA_SC_CONFIG
    headers_replaced = 0
    footers_replaced = 0
    stamp_affixed = False

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

        # 5. Affix Authentic Stamp & Signature
        if affix_stamp:
            stamp_affixed = affix_dealer_stamp_sale_certificate(page) or stamp_affixed

    return {
        "doc_type": "sale_certificate",
        "headers_replaced": headers_replaced,
        "footers_replaced": footers_replaced,
        "stamp_affixed": stamp_affixed
    }


def convert_document(input_path: str, output_path: str, hypothecation: str = None, new_date: str = None, affix_stamp: bool = True) -> dict:
    """
    Main conversion entry point.
    Processes each page individually, accurately handling standalone Tax Invoices,
    standalone Form 21 Sale Certificates, or multi-page documents containing BOTH!
    """
    doc = fitz.open(input_path)
    total_pages = len(doc)
    headers_replaced = 0
    footers_replaced = 0
    stamps_affixed = 0
    types_found = set()

    for page in doc:
        page_text = page.get_text()
        if "SALE CERTIFICATE" in page_text or "Form No .21" in page_text:
            types_found.add("sale_certificate")
            # --- Sale Certificate Processing ---
            shanti_hits = [h for h in page.search_for("Shanti Motors") if h.y0 < 100]
            if not shanti_hits:
                shanti_hits = [h for h in page.search_for("SHANTI MOTORS") if h.y0 < 100]

            if shanti_hits:
                page.add_redact_annot(fitz.Rect(54.0, 22.0, 440.0, 75.0), fill=(1, 1, 1))
                page.apply_redactions()
                cfg = ANNAPURNA_SC_CONFIG
                page.insert_text((56.7, 35.0), cfg["dealer_name"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
                page.insert_text((56.7, 46.0), cfg["address_line1"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
                page.insert_text((56.7, 57.0), cfg["address_line2"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
                page.insert_text((56.7, 68.0), cfg["dealer_auth"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
                headers_replaced += 1

            if hypothecation:
                update_hypothecation_sale_certificate(page, hypothecation)

            if new_date:
                update_date_sale_certificate(page, new_date)

            footer_hits = [h for h in page.search_for("Shanti Motors") if h.y0 > 200]
            if not footer_hits:
                footer_hits = [h for h in page.search_for("SHANTI MOTORS") if h.y0 > 200]

            for rect in footer_hits:
                expanded_rect = fitz.Rect(rect.x0 - 55, rect.y0 - 2, rect.x1 + 30, rect.y1 + 2)
                page.add_redact_annot(expanded_rect, fill=(1, 1, 1))
                page.apply_redactions()
                footer_text = ANNAPURNA_SC_CONFIG["footer_signatory"]
                text_len = fitz.get_text_length(footer_text, fontname="helv", fontsize=9.0)
                target_x = max(56.7, 570.0 - text_len)
                page.insert_text((target_x, 605.0), footer_text, fontsize=9.0, fontname="helv", color=(0, 0, 0))
                footers_replaced += 1

            if affix_stamp:
                if affix_dealer_stamp_sale_certificate(page):
                    stamps_affixed += 1

        else:
            # --- Tax Invoice Processing ---
            shanti_hits = page.search_for("SHANTI MOTORS")
            gstin_hits = page.search_for("23AQMPP0120E1ZE")
            header_hit = any(h.y0 < 200 for h in shanti_hits)
            is_invoice_face = header_hit or (gstin_hits and gstin_hits[0].y0 < 200)

            if is_invoice_face:
                types_found.add("invoice")
                header_rect = fitz.Rect(26.0, 106.0, 440.0, 170.0)
                page.add_redact_annot(header_rect, fill=(1, 1, 1))
                page.apply_redactions()
                cfg = ANNAPURNA_INVOICE_CONFIG
                page.insert_text((28.35, 120.5), cfg["dealer_name"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
                page.insert_text((28.35, 131.0), cfg["address_line1"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
                page.insert_text((28.35, 142.0), cfg["address_line2"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
                page.insert_text((28.35, 153.0), cfg["dealer_auth"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
                page.insert_text((28.35, 164.0), cfg["gstin_pan"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
                headers_replaced += 1

                if hypothecation:
                    update_hypothecation_invoice(page, hypothecation)

                if new_date:
                    update_date_invoice(page, new_date)

                footer_hits = [h for h in page.search_for("SHANTI MOTORS") if h.y0 > 200]
                if not footer_hits:
                    footer_hits = [h for h in page.search_for("M/S.SHANTI MOTORS") if h.y0 > 200]

                for rect in footer_hits:
                    expanded_rect = fitz.Rect(rect.x0 - 55, rect.y0 - 2, rect.x1 + 30, rect.y1 + 2)
                    page.add_redact_annot(expanded_rect, fill=(1, 1, 1))
                    page.apply_redactions()
                    footer_text = ANNAPURNA_INVOICE_CONFIG["footer_signatory"]
                    text_len = fitz.get_text_length(footer_text, fontname="helv", fontsize=9.0)
                    target_x = max(28.35, 577.05 - text_len)
                    page.insert_text((target_x, rect.y1 - 1.5), footer_text, fontsize=9.0, fontname="helv", color=(0, 0, 0))
                    footers_replaced += 1

                if affix_stamp:
                    if affix_dealer_stamp_invoice(page):
                        stamps_affixed += 1

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    if "sale_certificate" in types_found and "invoice" in types_found:
        final_type = "both"
    elif "sale_certificate" in types_found:
        final_type = "sale_certificate"
    else:
        final_type = "invoice"

    return {
        "doc_type": final_type,
        "pages_processed": total_pages,
        "headers_replaced": headers_replaced,
        "footers_replaced": footers_replaced,
        "stamps_affixed": stamps_affixed,
        "status": "success"
    }


# Aliases for backward compatibility
convert_shanti_to_annapurna = convert_document


def batch_convert(input_dir: str, output_dir: str, hypothecation: str = None, new_date: str = None, affix_stamp: bool = True, progress_callback=None) -> list:
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
            res = convert_document(in_file, out_file, hypothecation=hypothecation, new_date=new_date, affix_stamp=affix_stamp)
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
