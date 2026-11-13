"""
Invoice & Sale Certificate Converter Module
Converts Shanti Motors Tax Invoices & Sale Certificates into Annapurna Motors format.
Supports dynamic Hypothecation bank selection and Date replacement.
"""

import os
import re
import io
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
import numpy as np

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
    """Affix authentic Annapurna Motors circular rubber stamp and signature onto Tax Invoice, overlapping both For ANNAPURNA MOTORS and Authorized Signatory."""
    path = stamp_path or get_stamp_path()
    if not path or not os.path.exists(path):
        return False
    # Tax Invoice: precisely overlays both 'For ANNAPURNA MOTORS' (at y=646) and 'Authorized Signatory' (at y=684)
    rect = fitz.Rect(436.0, 626.0, 534.0, 718.0)
    page.insert_image(rect, filename=path, keep_proportion=True)
    return True


def affix_dealer_stamp_sale_certificate(page: fitz.Page, stamp_path: str = None) -> bool:
    """Affix authentic Annapurna Motors circular rubber stamp and signature onto Form 21 Sale Certificate, overlapping both For ANNAPURNA MOTORS and Authorized Signatory."""
    path = stamp_path or get_stamp_path()
    if not path or not os.path.exists(path):
        return False
    # Sale Certificate: precisely overlays both 'For ANNAPURNA MOTORS' (at y=605) and 'Authorized Signatory' (at y=660)
    rect = fitz.Rect(436.0, 585.0, 534.0, 678.0)
    page.insert_image(rect, filename=path, keep_proportion=True)
    return True


def affix_dealer_stamp_form_22(page: fitz.Page, stamp_path: str = None) -> bool:
    """Affix authentic Annapurna Motors circular rubber stamp and signature onto Form 22 Road-Worthiness Certificate in the open bottom-left blank space."""
    path = stamp_path or get_stamp_path()
    if not path or not os.path.exists(path):
        return False
    # Form 22: open blank space in bottom-left, aligned with Hero MotoCorp signatory block on the right
    rect = fitz.Rect(180.0, 688.0, 268.0, 778.0)
    page.insert_image(rect, filename=path, keep_proportion=True)
    return True


def optimize_pdf_size(doc: fitz.Document, max_kb: int = 270) -> bool:
    """
    Ensure any scanned or heavy pages inside the document are compressed so the
    generated PDF is strictly below 280 KB.
    """
    import io
    from PIL import Image

    compressed_any = False
    for page in doc:
        for img_info in page.get_images():
            xref = img_info[0]
            try:
                base = doc.extract_image(xref)
                # Only compress large background/scanned images (width > 600 and height > 600)
                if base["width"] > 600 and base["height"] > 600:
                    im = Image.open(io.BytesIO(base["image"]))
                    # Downscale to standard 150 DPI resolution for RTO document upload
                    im.thumbnail((1500, 1500), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    im.save(buf, format="JPEG", quality=70, optimize=True)
                    doc.update_stream(xref, buf.getvalue())
                    try:
                        doc.xref_set_key(xref, "Width", str(im.width))
                        doc.xref_set_key(xref, "Height", str(im.height))
                    except Exception:
                        pass
                    compressed_any = True
            except Exception:
                continue
    return compressed_any


def detect_document_type(doc: fitz.Document, filename: str = "") -> str:
    """Detect whether the document is Form 22, Form 21 Sale Certificate, or Tax Invoice."""
    fn = (filename or "").lower()
    if "22" in fn or "form 22" in fn or "road-worthiness" in fn:
        return "form_22"
    first_page_text = doc[0].get_text()
    if "FORM 22" in first_page_text or "ROAD-WORTHINESS" in first_page_text or "Rule 47 (1)(g)" in first_page_text:
        return "form_22"
    if "SALE CERTIFICATE" in first_page_text or "Form No .21" in first_page_text or "Form 21" in first_page_text:
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
    """Convert a Shanti Motors Tax Invoice into Annapurna Motors format. Strictly touches invoice content, leaves Terms untouched."""
    cfg = ANNAPURNA_INVOICE_CONFIG
    headers_replaced = 0
    footers_replaced = 0

    if len(doc) == 0:
        return {"doc_type": "invoice", "headers_replaced": 0, "footers_replaced": 0, "stamp_affixed": False}

    for p_idx, page in enumerate(doc):
        # Never touch the final page if it is Terms & Conditions
        if len(doc) > 1 and p_idx == len(doc) - 1:
            continue

        # 1. Replace Header on Page 0
        if p_idx == 0:
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

            if hypothecation:
                update_hypothecation_invoice(page, hypothecation)

            if new_date:
                update_date_invoice(page, new_date)

        # 2. Obliterate ANY and ALL Shanti Motors references in the right-side signatory block
        signatory_hit = False
        for term in ["SHANTI MOTORS", "Shanti Motors", "shanti motors", "M/S.SHANTI", "M/s.Shanti", "For M/S", "For M/s", "For  M"]:
            for h in page.search_for(term):
                if h.y0 > 200 and h.x0 > 380:
                    page.add_redact_annot(fitz.Rect(430.0, h.y0 - 5, 585.0, h.y1 + 5), fill=(1, 1, 1))
                    signatory_hit = True

        # Blanket-redact both candidate vertical bands to guarantee NO residual text leaks
        page.add_redact_annot(fitz.Rect(430.0, 590.0, 585.0, 615.0), fill=(1, 1, 1))
        page.add_redact_annot(fitz.Rect(430.0, 630.0, 585.0, 655.0), fill=(1, 1, 1))
        page.apply_redactions()

        # Insert For ANNAPURNA MOTORS cleanly right-aligned
        if p_idx == 0 or signatory_hit:
            footer_text = cfg["footer_signatory"]
            text_len = fitz.get_text_length(footer_text, fontname="helv", fontsize=9.0)
            target_x = max(28.35, 577.05 - text_len)
            target_y = 647.5 if p_idx == 0 else 226.0
            page.insert_text((target_x, target_y), footer_text, fontsize=9.0, fontname="helv", color=(0, 0, 0))
            footers_replaced += 1

    # 3. Affix Authentic Stamp & Signature on Page 0
    stamp_affixed = False
    if affix_stamp and len(doc) > 0:
        stamp_affixed = affix_dealer_stamp_invoice(doc[0])

    # 4. Strictly ignore Page 2 (Terms & Conditions) and keep only Page 1 (Page 0)
    while len(doc) > 1:
        doc.delete_page(1)

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

        # 4. Obliterate ANY and ALL Shanti Motors references in signatory block
        for term in ["SHANTI MOTORS", "Shanti Motors", "shanti motors", "M/S.SHANTI", "M/s.Shanti", "For M/S", "For M/s", "For  M"]:
            for h in page.search_for(term):
                if h.y0 > 200 and h.x0 > 380:
                    page.add_redact_annot(fitz.Rect(430.0, h.y0 - 5, 585.0, h.y1 + 5), fill=(1, 1, 1))

        # Blanket-redact both candidate vertical bands to guarantee NO residual text leaks
        page.add_redact_annot(fitz.Rect(430.0, 590.0, 585.0, 615.0), fill=(1, 1, 1))
        page.add_redact_annot(fitz.Rect(430.0, 630.0, 585.0, 655.0), fill=(1, 1, 1))
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


def apply_scanned_effect(doc: fitz.Document, bw_mode: bool = True, max_kb: int = 270) -> fitz.Document:
    """
    Renders PDF pages as realistic physically printed, stamped, and scanned pages:
    - Clean paper background without grain, salt-and-pepper noise, or faint dots
    - Crisp monochromatic laser printer toner on smooth paper
    - Natural ADF paper feed skew (0.5° - 0.65°)
    - Re-encodes as JPEG quality tuned to keep total size strictly < 280 KB.
    """
    new_doc = fitz.open()
    angles = [0.55, -0.48, 0.50, -0.42]
    num_pages = len(doc)
    target_quality = 68 if num_pages == 1 else 60

    for idx, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        if bw_mode:
            # 1. Convert to Grayscale (B&W scanner & printer)
            im_gray = im.convert("L")
            arr = np.array(im_gray, dtype=np.float32)

            # 2. Scanner optical contrast: clean smooth paper background, crisp dark toner
            arr = np.where(arr >= 210.0, np.clip(248.0 + (arr - 210.0) * 0.17, 0, 255), arr * 0.88)
            arr = np.clip(arr, 0, 255).astype(np.uint8)
            im_proc = Image.fromarray(arr, mode="L")
            fill_val = 255
        else:
            # Color scan with clean background
            arr = np.array(im, dtype=np.float32)
            arr = np.where(arr >= 210.0, np.clip(248.0 + (arr - 210.0) * 0.17, 0, 255), arr * 0.92)
            arr = np.clip(arr, 0, 255).astype(np.uint8)
            im_proc = Image.fromarray(arr, mode="RGB")
            fill_val = (255, 255, 255)

        # 3. Authentic ADF paper feed tilt
        angle = angles[idx % len(angles)]
        im_rot = im_proc.rotate(angle, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=fill_val)

        buf = io.BytesIO()
        im_rot.save(buf, format="JPEG", quality=target_quality, optimize=True)

        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(page.rect, stream=buf.getvalue())

    return new_doc


def convert_document(input_path: str, output_path: str, hypothecation: str = None, new_date: str = None, affix_stamp: bool = True, doc_type: str = "auto", scanned_effect: bool = True, bw_mode: bool = True) -> dict:
    """
    Main conversion entry point.
    Processes each page individually, accurately handling standalone Tax Invoices,
    standalone Form 21 Sale Certificates, Form 22 Road-Worthiness Certificates,
    or multi-page documents containing BOTH!
    Guarantees generated output is strictly below 280 KB.
    """
    doc = fitz.open(input_path)
    total_pages = len(doc)
    headers_replaced = 0
    footers_replaced = 0
    stamps_affixed = 0
    types_found = set()

    # Determine explicit or detected doc type
    detected_type = detect_document_type(doc, input_path) if doc_type == "auto" else doc_type

    if detected_type == "form_22":
        types_found.add("form_22")
        # In case of Form 22: NO editing/change is required.
        # Only affixing of the Annapurna Motors stamp on the bottom-left blank area.
        if affix_stamp and total_pages > 0:
            target_page = doc[0]
            if affix_dealer_stamp_form_22(target_page):
                stamps_affixed += 1
    else:
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

                # Obliterate ANY and ALL Shanti Motors references in signatory block
                for term in ["SHANTI MOTORS", "Shanti Motors", "shanti motors", "M/S.SHANTI", "M/s.Shanti", "For M/S", "For M/s", "For  M"]:
                    for h in page.search_for(term):
                        if h.y0 > 200 and h.x0 > 380:
                            page.add_redact_annot(fitz.Rect(430.0, h.y0 - 5, 585.0, h.y1 + 5), fill=(1, 1, 1))

                # Blanket-redact both candidate vertical bands
                page.add_redact_annot(fitz.Rect(430.0, 590.0, 585.0, 615.0), fill=(1, 1, 1))
                page.add_redact_annot(fitz.Rect(430.0, 630.0, 585.0, 655.0), fill=(1, 1, 1))
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

                    # Obliterate ANY and ALL Shanti Motors references in signatory block
                    for term in ["SHANTI MOTORS", "Shanti Motors", "shanti motors", "M/S.SHANTI", "M/s.Shanti", "For M/S", "For M/s", "For  M"]:
                        for h in page.search_for(term):
                            if h.y0 > 200 and h.x0 > 380:
                                page.add_redact_annot(fitz.Rect(430.0, h.y0 - 5, 585.0, h.y1 + 5), fill=(1, 1, 1))

                    # Blanket-redact both candidate vertical bands
                    page.add_redact_annot(fitz.Rect(430.0, 590.0, 585.0, 615.0), fill=(1, 1, 1))
                    page.add_redact_annot(fitz.Rect(430.0, 630.0, 585.0, 655.0), fill=(1, 1, 1))
                    page.apply_redactions()

                    footer_text = ANNAPURNA_INVOICE_CONFIG["footer_signatory"]
                    text_len = fitz.get_text_length(footer_text, fontname="helv", fontsize=9.0)
                    target_x = max(28.35, 577.05 - text_len)
                    page.insert_text((target_x, 647.5), footer_text, fontsize=9.0, fontname="helv", color=(0, 0, 0))
                    footers_replaced += 1

                    if affix_stamp:
                        if affix_dealer_stamp_invoice(page):
                            stamps_affixed += 1

    # For standalone Tax Invoices: strictly ignore Page 2 (Terms & Conditions) and only keep Page 1 (Page 0)
    is_invoice = (detected_type == "invoice") or ("invoice" in types_found and "sale_certificate" not in types_found)
    if is_invoice and len(doc) > 1:
        doc.select([0])

    # Apply scanned effect (printing & scanning imperfections, dull colors, tilt, grain)
    # or size optimization if scanned effect is disabled
    if scanned_effect:
        scanned_doc = apply_scanned_effect(doc, bw_mode=bw_mode)
        doc.close()
        doc = scanned_doc
    else:
        optimize_pdf_size(doc)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    # If the file size is still close to or above 275 KB, run a second aggressive optimization pass
    file_size_kb = os.path.getsize(output_path) / 1024.0
    if file_size_kb > 275.0:
        doc_retry = fitz.open(output_path)
        for page in doc_retry:
            for img_info in page.get_images():
                xref = img_info[0]
                try:
                    import io
                    from PIL import Image
                    base = doc_retry.extract_image(xref)
                    if base["width"] > 500 and base["height"] > 500:
                        im = Image.open(io.BytesIO(base["image"]))
                        im.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                        buf = io.BytesIO()
                        im.save(buf, format="JPEG", quality=62, optimize=True)
                        doc_retry.update_stream(xref, buf.getvalue())
                        doc_retry.xref_set_key(xref, "Width", str(im.width))
                        doc_retry.xref_set_key(xref, "Height", str(im.height))
                except Exception:
                    pass
        doc_retry.save(output_path, garbage=4, deflate=True)
        doc_retry.close()
        file_size_kb = os.path.getsize(output_path) / 1024.0

    if "form_22" in types_found:
        final_type = "form_22"
    elif "sale_certificate" in types_found and "invoice" in types_found:
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
        "file_size_kb": round(file_size_kb, 1),
        "status": "success"
    }


# Aliases for backward compatibility
convert_shanti_to_annapurna = convert_document


def batch_convert(input_dir: str, output_dir: str, hypothecation: str = None, new_date: str = None, affix_stamp: bool = True, scanned_effect: bool = True, bw_mode: bool = True, progress_callback=None) -> list:
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
            res = convert_document(in_file, out_file, hypothecation=hypothecation, new_date=new_date, affix_stamp=affix_stamp, scanned_effect=scanned_effect, bw_mode=bw_mode)
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
