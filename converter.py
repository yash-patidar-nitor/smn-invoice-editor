"""
Invoice Converter Module
Converts Shanti Motors invoices to Annapurna Motors invoices (and vice-versa).
Uses PyMuPDF (fitz) for high-fidelity redaction and vector text replacement.
"""

import os
import fitz  # PyMuPDF
# Dealership details for Annapurna Motors
ANNAPURNA_CONFIG = {
    "dealer_name": "ANNAPURNA MOTORS",
    "address_line1": "Khasra 193/1  Ward 15 Alirajpur Road",
    "address_line2": "KUKSHI DHAR MADHYA PRADESH 454331 State Code: 23 Contact #     9755820013",
    "dealer_auth": "Authorized Dealer: Hero MotoCorp Ltd.",
    "gstin_pan": "GSTIN #: 23AFTPG6974R1ZE PAN# AFTPG6974R",
    "footer_signatory": "For ANNAPURNA MOTORS",
    "gstin_num": "23AFTPG6974R1ZE"
}

# Dealership details for Shanti Motors
SHANTI_CONFIG = {
    "dealer_name": "M/S.SHANTI MOTORS",
    "address_line1": "NEAR NEW BUS STAND, PUNARVAS NISARPUR",
    "address_line2": "KUKSHI DHAR MADHYA PRADESH 454335 State Code: 23 Contact #     9131076286",
    "dealer_auth": "Authorized Representative of Dealer: Hero MotoCorp Ltd.",
    "gstin_pan": "GSTIN #: 23AQMPP0120E1ZE",
    "footer_signatory": "For M/S.SHANTI MOTORS",
    "gstin_num": "23AQMPP0120E1ZE"
}



def convert_shanti_to_annapurna(input_path: str, output_path: str, config: dict = None) -> dict:
    cfg = ANNAPURNA_CONFIG.copy()
    if config:
        cfg.update(config)

    doc = fitz.open(input_path)
    headers_replaced = 0
    footers_replaced = 0

    for page_idx, page in enumerate(doc):
        # 1. Replace Header Block
        shanti_hits = page.search_for("SHANTI MOTORS")
        header_hit = None
        for h in shanti_hits:
            if h.y0 < 200:
                header_hit = h
                break

        gstin_hits = page.search_for("23AQMPP0120E1ZE")

        if header_hit or (gstin_hits and gstin_hits[0].y0 < 200):
            x0 = 26.0
            y0 = 106.0
            x1 = 440.0
            y1 = 170.0

            header_rect = fitz.Rect(x0, y0, x1, y1)
            page.add_redact_annot(header_rect, fill=(1, 1, 1))
            page.apply_redactions()

            page.insert_text(
                (28.35, 120.5),
                cfg["dealer_name"],
                fontsize=9.0,
                fontname="helv",
                color=(0, 0, 0),
            )
            page.insert_text(
                (28.35, 131.0),
                cfg["address_line1"],
                fontsize=9.0,
                fontname="helv",
                color=(0, 0, 0),
            )
            page.insert_text(
                (28.35, 142.0),
                cfg["address_line2"],
                fontsize=9.0,
                fontname="helv",
                color=(0, 0, 0),
            )
            page.insert_text(
                (28.35, 153.0),
                cfg["dealer_auth"],
                fontsize=9.0,
                fontname="helv",
                color=(0, 0, 0),
            )
            page.insert_text(
                (28.35, 164.0),
                cfg["gstin_pan"],
                fontsize=9.0,
                fontname="helv",
                color=(0, 0, 0),
            )
            headers_replaced += 1

        # 2- Replace Footer Signatory
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
            target_y = rect.y1 - 1.5

            page.insert_text(
                (target_x, target_y),
                footer_text,
                fontsize=9.0,
                fontname="helv",
                color=(0, 0, 0),
            )
            footers_replaced += 1


    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    total_pages = len(doc)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    return {
        "pages_processed": total_pages,
        "headers_replaced": headers_replaced,
        "footers_replaced": footers_replaced,
        "status": "success" if (headers_replaced > 0 or footers_replaced > 0) else "no_targets_found"
    }



def convert_annapurna_to_shanti(input_path: str, output_path: str, config: dict = None) -> dict:
    cfg = SHANTI_CONFIG.copy()
    if config:
        cfg.update(config)

    doc = fitz.open(input_path)
    headers_replaced = 0
    footers_replaced = 0

    for page_idx, page in enumerate(doc):
        ann_hits = [h for h in page.search_for("ANNAPURNA MOTORS") if h.y0 < 200]
        gstin_hits = [h for h in page.search_for("23AFTPG6974R1ZE") if h.y0 < 200]

        if ann_hits or gstin_hits:
            x0 = 26.0
            y0 = 106.0
            x1 = 440.0
            y1 = 170.0

            header_rect = fitz.Rect(x0, y0, x1, y1)
            page.add_redact_annot(header_rect, fill=(1, 1, 1))
            page.apply_redactions()

            header_text = (
                f"{cfg['dealer_name']}\n"
                f"{cfg['address_line1']}\n"
                f"{cfg['address_line2']}\n"
                f"{cfg['dealer_auth']}\n"
                f"{cfg['gstin_pan']}"
            )
            page.insert_textbox(
                fitz.Rect(28.35, 110.0, 420.0, 170.0),
                header_text,
                fontsize=8.5,
                fontname="helv",
                color=(0, 0, 0),
                align=0
            )
            headers_replaced += 1

        footer_hits = [h for h in page.search_for("ANNAPURNA MOTORS") if h.y0 > 200]
        for rect in footer_hits:
            expanded_rect = fitz.Rect(rect.x0 - 50, rect.y0 - 2, rect.x1 + 30, rect.y1 + 2)
            page.add_redact_annot(expanded_rect, fill=(1, 1, 1))
            page.apply_redactions()

            footer_text = cfg["footer_signatory"]
            text_len = fitz.get_text_length(footer_text, fontname="helv", fontsize=9.0)
            target_x = max(28.35, 577.05 - text_len)
            target_y = rect.y1 - 1.5

            page.insert_text(
                (target_x, target_y),
                footer_text,
                fontsize=9.0,
                fontname="helv",
                color=(0, 0, 0),
            )
            footers_replaced += 1

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    total_pages = len(doc)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    return {
        "pages_processed": total_pages,
        "headers_replaced": headers_replaced,
        "footers_replaced": footers_replaced,
        "status": "success" if (headers_replaced > 0 or footers_replaced > 0) else "no_targets_found"
    }



def batch_convert(input_dir: str, output_dir: str, direction: str = 'shanti_to_annapurna', config: dict = None, progress_callback = None) -> list:
    os.makedirs(output_dir, exist_ok=True)
    results = []
    files = [p for p in sorted(os.listdir(input_dir)) if p.lower().endswith('.pdf')]
    total = len(files)
    
    for idx, filename in enumerate(files):
        in_file = os.path.join(input_dir, filename)
        prefix = "annapurna_" if direction == "shanti_to_annapurna" else "shanti_"
        out_file = os.path.join(output_dir, f"{prefix}{filename}")
        
        try:
            if direction == "shanti_to_annapurna":
                res = convert_shanti_to_annapurna(in_file, out_file, config)
            else:
                res = convert_annapurna_to_shanti(in_file, out_file, config)
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


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Hero Invoice Dealership Converter")
    parser.add_argument("--input", "-i", required=True, help="Input PDF file or directory")
    parser.add_argument("--output", "-o", required=True, help="Output PDF file or directory")
    parser.add_argument("--direction", "-d", choices=["shanti_to_annapurna", "annapurna_to_shanti"], 
                        default="shanti_to_annapurna", help="Conversion direction")
    
    args = parser.parse_args()
    
    if os.path.isdir(args.input):
        print(f"Batch processing directory: {args.input} -> {args.output}")
        out_list = batch_convert(args.input, args.output, direction=args.direction)
        for item in out_list:
            status_str = item['status'].upper()
            fname = item['filename']
            out_p = item.get('output_path', '')
            print(f"[{status_str}] {fname} -> {out_p}")
    else:
        print(f"Processing single file: {args.input} -> {args.output}")
        if args.direction == "shanti_to_annapurna":
            res = convert_shanti_to_annapurna(args.input, args.output)
        else:
            res = convert_annapurna_to_shanti(args.input, args.output)
        print("Result:", res)
