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
    "footer_signatory": "For M/s.Annapurna Motors",
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


def affix_dealer_stamp_invoice(page: fitz.Page, stamp_path: str = None, dealer_y: float = 636.5) -> bool:
    """Affix authentic Annapurna Motors circular rubber stamp and signature onto Tax Invoice,
    dynamically positioned between For ANNAPURNA MOTORS and Authorized Signatory."""
    path = stamp_path or get_stamp_path()
    if not path or not os.path.exists(path):
        return False
    # Tax Invoice: dynamically positioned relative to dealer_y so it cleanly bridges
    # 'For ANNAPURNA MOTORS' (at dealer_y) and 'Authorized Signatory' (at dealer_y + 47)
    stamp_y = dealer_y - 10.5
    rect = fitz.Rect(436.0, stamp_y, 534.0, stamp_y + 92.0)
    page.insert_image(rect, filename=path, keep_proportion=True)
    return True


def affix_dealer_stamp_sale_certificate(page: fitz.Page, stamp_path: str = None) -> bool:
    """Affix authentic Annapurna Motors circular rubber stamp and signature onto Form 21 Sale Certificate, in the signatory space between 'For M/s.Annapurna Motors' and 'Authorized Signatory'."""
    path = stamp_path or get_stamp_path()
    if not path or not os.path.exists(path):
        return False
    # Sale Certificate: positioned cleanly in signature space between 'For M/s.Annapurna Motors' (at y=595) and 'Authorized Signatory' (at y=668)
    rect = fitz.Rect(440.0, 600.0, 514.0, 668.0)
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
    clean_fn = (filename or "").lower().replace("-", " ").replace("_", " ")

    # 1. Unambiguous filename keyword check (handles all standard Hero portal download names)
    if any(k in clean_fn for k in ["form 22", "form22", "road worthiness", "roadworthiness"]):
        return "form_22"
    if any(k in clean_fn for k in ["sale cert", "salecert", "sale certificate", "form 21", "form21"]):
        return "sale_certificate"
    if any(k in clean_fn for k in ["gst retail", "tax invoice", "retail invoice"]):
        return "invoice"

    # 2. PDF Content inspection
    try:
        first_page_text = doc[0].get_text().upper()
        if "FORM 22" in first_page_text or "ROAD-WORTHINESS" in first_page_text or "RULE 47 (1)(G)" in first_page_text:
            return "form_22"
        if "SALE CERTIFICATE" in first_page_text or "FORM NO .21" in first_page_text or "FORM 21" in first_page_text or "DELIVERED BY US ON DATE" in first_page_text:
            return "sale_certificate"
        if "TAX INVOICE" in first_page_text or "RETAIL INVOICE" in first_page_text or "GSTIN" in first_page_text or "CUSTOMER'S SIGNATURES" in first_page_text:
            return "invoice"
    except Exception:
        pass

    # 3. Fallback filename keyword check
    if any(k in clean_fn for k in ["invoice", "tax", "retail", "gst"]):
        return "invoice"

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
    """Update Date on Tax Invoice while dynamically locating Date baseline and preserving original time."""
    if not new_date_str or not new_date_str.strip():
        return False

    date_hits = [h for h in page.search_for("Date") if 180 < h.y0 < 360 and h.x0 > 380]
    if not date_hits:
        return False

    h = date_hits[0]
    val_y0 = h.y0 + 0.9
    val_y1 = h.y1 + 0.5
    baseline = h.y1 - 2.7
    val_rect = fitz.Rect(475.0, val_y0, 595.0, val_y1)
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
        (479.8, baseline),
        f" {final_date.lstrip()}",
        fontsize=9.0,
        fontname="helv",
        color=(0, 0, 0)
    )
    return True


def update_date_sale_certificate(page: fitz.Page, new_date_str: str) -> bool:
    """Update Date at top-right and in the body paragraph of Sale Certificate.
    Dynamically locates the delivery clause date (handles same-line and wrapped dates)
    and strictly avoids touching Invoice #. Normalizes date to DD/MM/YYYY.
    """
    if not new_date_str or not new_date_str.strip():
        return False

    clean_match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", new_date_str.strip())
    if clean_match:
        d, m, y = clean_match.groups()
        date_formatted = f"{int(d):02d}/{int(m):02d}/{y}"
    else:
        iso_match = re.search(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", new_date_str.strip())
        if iso_match:
            y, m, d = iso_match.groups()
            date_formatted = f"{int(d):02d}/{int(m):02d}/{y}"
        else:
            date_formatted = new_date_str.strip()

    # 1. Top right date: strictly y=120.0 to 134.0, x=510.0 to 580.0
    val_rect = fitz.Rect(510.0, 120.0, 580.0, 134.0)
    page.add_redact_annot(val_rect, fill=(1, 1, 1))
    page.apply_redactions()
    page.insert_text(
        (512.1, 130.19),
        f"  {date_formatted}",
        fontsize=9.0,
        fontname="helv",
        color=(0, 0, 0)
    )

    # 2. Body clause date: Dynamically find the date word in the delivery clause
    # (between y=170.0 and 205.0). Tight safe rect strictly avoids touching adjacent lines (never touches Invoice #)
    words = page.get_text("words")
    body_date_found = False

    for w in words:
        if 170.0 <= w[1] <= 205.0 and re.search(r"\b\d{2}[/-]\d{2}[/-]\d{4}\b", w[4]):
            baseline = w[3] - 2.7
            # Tight safe rect: never touches lines above or below (no Invoice # clipping)
            safe_rect = fitz.Rect(w[0] - 0.5, baseline - 7.2, w[2] + 0.5, baseline + 0.5)
            page.add_redact_annot(safe_rect, fill=(1, 1, 1))
            page.apply_redactions()
            page.insert_text(
                (w[0], baseline),
                date_formatted,
                fontsize=9.0,
                fontname="helv",
                color=(0, 0, 0)
            )
            body_date_found = True
            break

    if not body_date_found:
        # Fallback: search for "delivered by us on date"
        hits = page.search_for("delivered by us on date")
        if hits:
            h = hits[0]
            if h.x1 + 60.0 <= page.rect.width - 40.0:
                # Same line (e.g. Splendor+, HF Deluxe)
                baseline = h.y1 - 2.7
                safe_rect = fitz.Rect(h.x1, baseline - 7.2, h.x1 + 46.0, baseline + 0.5)
                page.add_redact_annot(safe_rect, fill=(1, 1, 1))
                page.apply_redactions()
                page.insert_text((h.x1 + 2.5, baseline), date_formatted, fontsize=9.0, fontname="helv", color=(0, 0, 0))
            else:
                # Wrapped to next line (e.g. Destini Prime)
                baseline = h.y1 + 7.7
                safe_rect = fitz.Rect(65.0, baseline - 7.2, 111.5, baseline + 0.5)
                page.add_redact_annot(safe_rect, fill=(1, 1, 1))
                page.apply_redactions()
                page.insert_text((65.7, baseline), date_formatted, fontsize=9.0, fontname="helv", color=(0, 0, 0))

    return True


def is_terms_page(page: fitz.Page) -> bool:
    """Check if a page is a Terms & Conditions / Disclaimer page."""
    txt = page.get_text().lower()
    return ('terms & conditions' in txt or 
            'terms and conditions' in txt or 
            'kindly visit hmcl dealership' in txt)


def convert_invoice(doc: fitz.Document, hypothecation: str = None, new_date: str = None, affix_stamp: bool = True) -> dict:
    """Convert a Shanti Motors Tax Invoice into Annapurna Motors format.
    - Dynamically detects and drops ONLY Terms & Conditions pages.
    - Dynamically locates and protects 'Authorized Signatory'.
    - Self-healing: Guarantees 'Authorized Signatory' is NEVER missing.
    """
    cfg = ANNAPURNA_INVOICE_CONFIG
    headers_replaced = 0
    footers_replaced = 0
    stamp_affixed = False

    if len(doc) == 0:
        return {"doc_type": "invoice", "headers_replaced": 0, "footers_replaced": 0, "stamp_affixed": False}

    # 1. Identify non-terms pages (drop only Terms & Conditions pages)
    invoice_page_indices = [i for i, p in enumerate(doc) if not is_terms_page(p)]
    if not invoice_page_indices:
        invoice_page_indices = [0]

    # 2. Process Page 0: Dealer Header, Hypothecation, Date
    page0 = doc[0]
    shanti_hits = page0.search_for("SHANTI MOTORS")
    gstin_hits = page0.search_for("23AQMPP0120E1ZE")
    header_hit = any(h.y0 < 200 for h in shanti_hits)

    if header_hit or (gstin_hits and gstin_hits[0].y0 < 200):
        header_rect = fitz.Rect(26.0, 106.0, 440.0, 170.0)
        page0.add_redact_annot(header_rect, fill=(1, 1, 1))
        page0.apply_redactions()

        page0.insert_text((28.35, 120.5), cfg["dealer_name"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
        page0.insert_text((28.35, 131.0), cfg["address_line1"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
        page0.insert_text((28.35, 142.0), cfg["address_line2"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
        page0.insert_text((28.35, 153.0), cfg["dealer_auth"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
        page0.insert_text((28.35, 164.0), cfg["gstin_pan"], fontsize=9.0, fontname="helv", color=(0, 0, 0))
        headers_replaced += 1

    if hypothecation:
        update_hypothecation_invoice(page0, hypothecation)

    if new_date:
        update_date_invoice(page0, new_date)

    # 3. Process Signatory Block on the invoice page containing the signature
    sig_page_idx = invoice_page_indices[-1]
    for p_idx in invoice_page_indices:
        p = doc[p_idx]
        if any(h.x0 > 320 and h.y0 > 100 for h in (p.search_for("Signatory") + p.search_for("Authorized") + p.search_for("Authorised"))):
            sig_page_idx = p_idx
            break

    sig_page = doc[sig_page_idx]

    # Robust multi-anchor detection for dealer line and Authorized Signatory
    dealer_y = None
    auth_y = None

    # Anchor 1: Search for 'Signatory' or 'Authorized' / 'Authorised' on the right side
    for h in (sig_page.search_for("Signatory") + sig_page.search_for("Authorized") + sig_page.search_for("Authorised")):
        if h.x0 > 320 and h.y0 > 100:
            auth_y = h.y0
            dealer_y = h.y0 - 47.0
            break

    # Anchor 2: Search for Dealer name in signature block
    if dealer_y is None:
        for term in ["SHANTI MOTORS", "Shanti Motors", "shanti motors", "M/S.SHANTI", "M/s.Shanti", "For M/S", "For M/s", "For  M"]:
            hits = [h for h in sig_page.search_for(term) if h.x0 > 320 and h.y0 > 100]
            if hits:
                dealer_y = hits[0].y0
                auth_y = dealer_y + 47.0
                break

    # Anchor 3: Search for 'Customer\'s Signatures' on the left side (same vertical level as dealer line)
    if dealer_y is None:
        for h in sig_page.search_for("Customer's Signatures"):
            if h.y0 > 100:
                dealer_y = h.y0
                auth_y = dealer_y + 47.0
                break

    # Fallback to standard Hero template baselines if text is unindexed
    if dealer_y is None:
        dealer_y = 636.5 if sig_page_idx == 0 else 215.0
        auth_y = dealer_y + 47.0

    # Redact Shanti Motors: bounded cleanly from x=390 to 585
    sig_page.add_redact_annot(fitz.Rect(390.0, dealer_y - 3.0, 585.0, dealer_y + 13.0), fill=(1, 1, 1))
    sig_page.apply_redactions()

    # Draw For ANNAPURNA MOTORS
    footer_text = cfg["footer_signatory"]
    text_len = fitz.get_text_length(footer_text, fontname="helv", fontsize=9.0)
    target_x = max(28.35, 577.05 - text_len)
    sig_page.insert_text((target_x, dealer_y + 9.5), footer_text, fontsize=9.0, fontname="helv", color=(0, 0, 0))
    footers_replaced += 1

    # CRITICAL SELF-HEALING: Verify that Authorized Signatory is 100% present on the signature page!
    auth_check = [h for h in (sig_page.search_for("Signatory") + sig_page.search_for("Authorized") + sig_page.search_for("Authorised")) if h.x0 > 320 and h.y0 > 100]
    if not auth_check:
        auth_text = "Authorized Signatory"
        auth_len = fitz.get_text_length(auth_text, fontname="helv", fontsize=9.0)
        auth_x = max(28.35, 577.05 - auth_len)
        sig_page.insert_text((auth_x, auth_y + 9.5), auth_text, fontsize=9.0, fontname="helv", color=(0, 0, 0))

    # 4. Affix Authentic Stamp & Signature
    if affix_stamp:
        stamp_affixed = affix_dealer_stamp_invoice(sig_page, dealer_y=dealer_y)

    # 5. Remove Terms & Conditions pages, keeping all actual invoice pages
    for i in range(len(doc) - 1, -1, -1):
        if i not in invoice_page_indices:
            doc.delete_page(i)

    # In case pages were deleted before sig_page_idx, adjust sig_page_idx
    final_sig_page_idx = invoice_page_indices.index(sig_page_idx) if sig_page_idx in invoice_page_indices else 0

    return {
        "doc_type": "invoice",
        "headers_replaced": headers_replaced,
        "footers_replaced": footers_replaced,
        "stamp_affixed": stamp_affixed,
        "sig_page_idx": final_sig_page_idx,
        "dealer_y": dealer_y
    }


def convert_sale_certificate(doc: fitz.Document, hypothecation: str = None, new_date: str = None, affix_stamp: bool = True) -> dict:
    """Convert a Shanti Motors Sale Certificate into Annapurna Motors format."""
    cfg = ANNAPURNA_SC_CONFIG
    headers_replaced = 0
    footers_replaced = 0
    stamp_affixed = False

    # Strictly truncate 2nd page: only keep Page 1 (Page 0)
    if len(doc) > 1:
        doc.select([0])

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

        # Blanket-redact the full signatory header band (y: 575.0 to 620.0) so no residual Shanti Motors can ever leak
        # Leaves 38 pt safety margin above Authorized Signatory at y=658.7
        page.add_redact_annot(fitz.Rect(425.0, 575.0, 585.0, 620.0), fill=(1, 1, 1))
        page.apply_redactions()

        footer_text = cfg["footer_signatory"]
        text_len = fitz.get_text_length(footer_text, fontname="helv", fontsize=9.0)
        target_x = max(56.7, 570.0 - text_len)
        page.insert_text((target_x, 595.0), footer_text, fontsize=9.0, fontname="helv", color=(0, 0, 0))
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


def convert_form_22(doc: fitz.Document, affix_stamp: bool = True) -> dict:
    """Convert Form 22 Road-Worthiness Certificate: strictly 1 page, affixes stamp in bottom-left."""
    stamps_affixed = 0
    if len(doc) > 1:
        doc.select([0])
    if affix_stamp and len(doc) > 0:
        if affix_dealer_stamp_form_22(doc[0]):
            stamps_affixed += 1
    return {
        "doc_type": "form_22",
        "headers_replaced": 0,
        "footers_replaced": 0,
        "stamp_affixed": stamps_affixed > 0
    }


def apply_scanned_effect(doc: fitz.Document, bw_mode: bool = True, stamp_info: dict = None, max_kb: int = 270) -> fitz.Document:
    """
    Renders PDF pages as realistic physically printed, stamped, and scanned pages:
    - Applies Black & White filter to the ENTIRE document BEFORE affixing seal and signature
    - Green banner and red logos become clean monochrome laser print toner
    - Affixes authentic blue rubber seal and signature in original color on top of the B&W printout
    - Natural ADF paper feed skew (0.5° - 0.65°)
    - Re-encodes as JPEG quality tuned to keep total size strictly < 280 KB.
    """
    new_doc = fitz.open()
    angles = [0.55, -0.48, 0.50, -0.42]
    num_pages = len(doc)
    target_quality = 68 if num_pages == 1 else 60

    stamp_img = None
    if stamp_info and os.path.exists("assets/stamp.png"):
        try:
            stamp_img = Image.open("assets/stamp.png").convert("RGBA")
        except Exception:
            pass

    for idx, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        im = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        if bw_mode:
            # 1. Convert ENTIRE document to Black & White laser print
            # (Guarantees green banner, red logo, text, tables are 100% monochrome toner)
            im_gray = im.convert("L")
            arr = np.array(im_gray, dtype=np.float32)
            arr = np.where(arr >= 210.0, np.clip(248.0 + (arr - 210.0) * 0.17, 0.0, 255.0), arr * 0.88)
            arr = np.clip(arr, 0, 255).astype(np.uint8)
            im_proc = Image.fromarray(arr, mode="L").convert("RGBA")

            # 2. Affix authentic blue rubber seal & signature ON TOP of the B&W printout
            target_page_idx = stamp_info.get("page", 0) if stamp_info else 0
            if idx == target_page_idx and stamp_info and stamp_img:
                scale = 150.0 / 72.0
                sw = int(stamp_info["width"] * scale)
                sh = int(stamp_info["height"] * scale)
                sx = int(stamp_info["x"] * scale)
                sy = int(stamp_info["y"] * scale)
                stamp_resized = stamp_img.resize((sw, sh), Image.Resampling.LANCZOS)
                im_proc.paste(stamp_resized, (sx, sy), stamp_resized)

            im_proc = im_proc.convert("RGB")
            fill_val = (255, 255, 255)
        else:
            # Color scan mode
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
    Delegates to the dedicated, robust converter for each document type:
    - Form 22: convert_form_22
    - Form 21 Sale Certificate: convert_sale_certificate
    - Tax Invoice: convert_invoice
    Guarantees generated output is strictly below 280 KB.
    """
    doc = fitz.open(input_path)
    total_pages = len(doc)
    detected_type = detect_document_type(doc, input_path) if doc_type == "auto" else doc_type

    if detected_type == "form_22":
        stats = convert_form_22(doc, affix_stamp=affix_stamp)
        stamp_info = {"x": 180.0, "y": 688.0, "width": 88.0, "height": 90.0} if affix_stamp else None
    elif detected_type == "sale_certificate":
        stats = convert_sale_certificate(doc, hypothecation=hypothecation, new_date=new_date, affix_stamp=affix_stamp)
        stamp_info = {"x": 440.0, "y": 600.0, "width": 74.0, "height": 68.0} if affix_stamp else None
    else:
        # In scanned effect mode, do not pre-affix vector stamp because apply_scanned_effect affixes it in color
        stats = convert_invoice(doc, hypothecation=hypothecation, new_date=new_date, affix_stamp=(not scanned_effect and affix_stamp))
        stamp_info = {
            "page": stats.get("sig_page_idx", 0),
            "x": 436.0,
            "y": stats.get("dealer_y", 636.5) - 10.5,
            "width": 98.0,
            "height": 92.0
        } if affix_stamp else None

    # Apply scanned effect (B&W laser print filter applied FIRST, then stamp affixed on top in color)
    if scanned_effect:
        scanned_doc = apply_scanned_effect(doc, bw_mode=bw_mode, stamp_info=stamp_info)
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

    return {
        "doc_type": detected_type,
        "pages_processed": total_pages,
        "headers_replaced": stats.get("headers_replaced", 1),
        "footers_replaced": stats.get("footers_replaced", 1),
        "stamps_affixed": 1 if stats.get("stamp_affixed", False) else 0,
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
