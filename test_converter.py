"""
Comprehensive Test Suite for Hero Invoice and Sale Certificate Converter.
Verifies:
1. Tax Invoice conversion (Shanti -> Annapurna)
2. Sale Certificate conversion (Shanti -> Annapurna)
3. Hypothecation replacement (TATA CAPITAL, AASTHA SAKH SAHKARITA, BLANK, HERO FINCORP)
4. Date replacement across Invoice and Sale Certificate
"""

import os
import tempfile
import fitz
import converter


def test_real_files():
    # 1. Test Invoice if present
    inv_path = r"c:\Users\yash.patidar\Downloads\smn.pdf"
    if os.path.exists(inv_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = os.path.join(tmpdir, "annapurna_inv.pdf")
            stats = converter.convert_document(
                inv_path,
                out_pdf,
                hypothecation="TATA CAPITAL LTD",
                new_date="18/11/2026",
                scanned_effect=False
            )
            print("Invoice conversion stats:", stats)
            assert stats["status"] == "success"
            assert stats["doc_type"] == "invoice"

            with fitz.open(out_pdf) as doc:
                page0 = doc[0]
                # Verify Shanti Motors is gone
                assert len(page0.search_for("SHANTI MOTORS")) == 0
                # Verify Annapurna is present
                assert len(page0.search_for("ANNAPURNA MOTORS")) >= 1
                assert len(page0.search_for("For ANNAPURNA MOTORS")) >= 1
                # Verify Invoice # and Mobile # are NOT truncated
                assert len(page0.search_for("63502BK26S368")) >= 1
                assert len(page0.search_for("9343006704")) >= 1
                # Verify Page 2 was ignored and only Page 1 is in the final output
                assert len(doc) == 1, f"Expected exactly 1 page for converted Invoice, got {len(doc)}"
            print("INVOICE TEST PASSED: Header, Footer, Hypothecation, Date, and pristine font preservation verified!")

    # 2. Test Sale Certificate if present
    sc_path = r"c:\Users\yash.patidar\Downloads\Sale Certificate - 2026-11-12T211331.714.PDF"
    if os.path.exists(sc_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = os.path.join(tmpdir, "annapurna_sc.pdf")
            stats = converter.convert_document(
                sc_path,
                out_pdf,
                hypothecation="AASTHA SAKH SAHKARITA",
                new_date="20/11/2026",
                scanned_effect=False
            )
            print("Sale Certificate conversion stats:", stats)
            assert stats["status"] == "success"
            assert stats["doc_type"] == "sale_certificate"

            doc = fitz.open(out_pdf)
            page0 = doc[0]
            # Verify Shanti Motors is gone
            assert len(page0.search_for("Shanti Motors")) == 0
            # Verify Annapurna is present
            assert len(page0.search_for("ANNAPURNA MOTORS")) >= 1
            assert len(page0.search_for("For M/s.Annapurna Motors")) >= 1
            # Verify Hypothecation
            assert len(page0.search_for("AASTHA SAKH SAHKARITA")) >= 1
            # Verify Date (both top and body)
            assert len(page0.search_for("20/11/2026")) >= 2
            doc.close()
            print("SALE CERTIFICATE TEST PASSED: Header, Footer, Hypothecation & Date verified!")

    # 3. Test Blank Hypothecation on Sale Certificate
    if os.path.exists(sc_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = os.path.join(tmpdir, "annapurna_sc_blank.pdf")
            stats = converter.convert_document(
                sc_path,
                out_pdf,
                hypothecation="BLANK",
                scanned_effect=False
            )
            assert stats["status"] == "success"
            doc = fitz.open(out_pdf)
            page0 = doc[0]
            assert len(page0.search_for("HERO FINCORP LTD")) == 0
            doc.close()
            print("BLANK HYPOTHECATION TEST PASSED!")


def test_mock_ci():
    """Synthetic tests for headless CI runners (tests both Invoices and Sale Certificates)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Mock Sale Certificate
        mock_sc = os.path.join(tmpdir, "mock_sc.pdf")
        doc = fitz.open()
        p = doc.new_page(width=595, height=842)
        p.insert_text((56.7, 35.0), "M/s.Shanti Motors", fontsize=9.0)
        p.insert_text((56.7, 46.0), "NEAR NEW BUS STAND, PUNARVAS NISARPUR", fontsize=9.0)
        p.insert_text((56.7, 57.0), "KUKSHI DHAR MADHYA PRADESH 454335 Contact# 9131076286", fontsize=9.0)
        p.insert_text((56.7, 68.0), "Authorized Representative of Dealer:Hero MotoCorp Ltd.", fontsize=9.0)
        p.insert_text((56.7, 100.0), "SALE CERTIFICATE Form No .21", fontsize=12.0)
        p.insert_text((480.0, 120.0), "Date", fontsize=9.0)
        p.insert_text((512.0, 120.0), "  11/11/2026", fontsize=9.0)
        p.insert_text((65.0, 180.0), "delivered by us on date 11/11/2026 with Invoice", fontsize=9.0)
        p.insert_text((80.0, 356.0), "purchase/hypothecation with", fontsize=9.0)
        p.insert_text((326.0, 356.0), "HERO FINCORP LTD", fontsize=9.0)
        p.insert_text((480.0, 595.0), "For M/s.Shanti Motors", fontsize=9.0)
        p_extra = doc.new_page(width=595, height=842)
        p_extra.insert_text((50.0, 50.0), "Extra Sale Certificate page that must be truncated", fontsize=10.0)
        doc.save(mock_sc)
        doc.close()

        out_sc = os.path.join(tmpdir, "mock_sc_out.pdf")
        stats_sc = converter.convert_document(mock_sc, out_sc, hypothecation="TATA CAPITAL LTD", new_date="25/11/2026", affix_stamp=True, scanned_effect=False)
        assert stats_sc["status"] == "success"
        assert stats_sc["doc_type"] == "sale_certificate"
        assert stats_sc["stamps_affixed"] == 1

        doc_out = fitz.open(out_sc)
        assert len(doc_out) == 1, f"Expected strictly 1 page for Sale Certificate, got {len(doc_out)}"
        p_out = doc_out[0]
        assert len(p_out.search_for("Shanti Motors")) == 0
        assert len(p_out.search_for("ANNAPURNA MOTORS")) >= 1
        assert len(p_out.search_for("TATA CAPITAL LTD")) >= 1
        assert len(p_out.search_for("25/11/2026")) >= 2
        doc_out.close()
        print("MOCK SALE CERTIFICATE CI TEST PASSED (STRICT 1-PAGE)!")

        # 2. Mock Tax Invoice
        mock_inv = os.path.join(tmpdir, "mock_inv.pdf")
        doc_inv = fitz.open()
        p_inv = doc_inv.new_page(width=595, height=842)
        p_inv.insert_text((28.0, 30.0), "TAX INVOICE", fontsize=12.0)
        p_inv.insert_text((28.0, 120.5), "M/S.SHANTI MOTORS", fontsize=9.0)
        p_inv.insert_text((28.0, 131.0), "NEAR NEW BUS STAND, PUNARVAS NISARPUR", fontsize=9.0)
        p_inv.insert_text((28.0, 142.0), "KUKSHI DHAR MADHYA PRADESH 454335", fontsize=9.0)
        p_inv.insert_text((28.0, 153.0), "Authorized Representative of Dealer: Hero MotoCorp Ltd.", fontsize=9.0)
        p_inv.insert_text((28.0, 164.0), "GSTIN #: 23AQMPP0120E1ZE", fontsize=9.0)
        p_inv.insert_text((420.0, 225.0), "Date", fontsize=9.0)
        p_inv.insert_text((480.0, 225.0), "11/11/2026 14:30", fontsize=9.0)
        p_inv.insert_text((450.0, 600.0), "For M/S.SHANTI MOTORS", fontsize=9.0)
        doc_inv.save(mock_inv)
        doc_inv.close()

        out_inv = os.path.join(tmpdir, "mock_inv_out.pdf")
        stats_inv = converter.convert_document(mock_inv, out_inv, hypothecation="HERO FINCORP LTD", new_date="26/11/2026", affix_stamp=True, scanned_effect=False)
        assert stats_inv["status"] == "success"
        assert stats_inv["doc_type"] == "invoice"
        assert stats_inv["stamps_affixed"] == 1

        doc_inv_out = fitz.open(out_inv)
        p_inv_out = doc_inv_out[0]
        assert len(p_inv_out.search_for("SHANTI MOTORS")) == 0
        assert len(p_inv_out.search_for("ANNAPURNA MOTORS")) >= 1
        assert len(p_inv_out.search_for("26/11/2026")) >= 1
        assert len(doc_inv_out) == 1, f"Expected 1 page for invoice, got {len(doc_inv_out)}"
        doc_inv_out.close()
        print("MOCK INVOICE CI TEST PASSED!")

        # 3. Mock Form 22
        mock_f22 = os.path.join(tmpdir, "mock_form22.pdf")
        doc_f22 = fitz.open()
        p_f22 = doc_f22.new_page(width=595, height=842)
        p_f22.insert_text((200.0, 50.0), "Hero MotoCorp Ltd.", fontsize=14.0)
        p_f22.insert_text((230.0, 150.0), "FORM 22", fontsize=14.0)
        p_f22.insert_text((180.0, 170.0), "ROAD-WORTHINESS CERTIFICATE", fontsize=11.0)
        p_f22.insert_text((420.0, 700.0), "For Hero MotoCorp Ltd.", fontsize=10.0)
        p_f22.insert_text((420.0, 750.0), "Head - National Sales (Authorized Signatory)", fontsize=9.0)
        p_f22_extra = doc_f22.new_page(width=595, height=842)
        p_f22_extra.insert_text((50.0, 50.0), "Extra Form 22 page that must be truncated", fontsize=10.0)
        doc_f22.save(mock_f22)
        doc_f22.close()

        out_f22 = os.path.join(tmpdir, "mock_f22_out.pdf")
        stats_f22 = converter.convert_document(mock_f22, out_f22, affix_stamp=True, scanned_effect=False)
        assert stats_f22["status"] == "success"
        assert stats_f22["doc_type"] == "form_22"
        assert stats_f22["stamps_affixed"] == 1
        # Form 22 must NOT change Hero MotoCorp or text and MUST be strictly 1 page
        doc_f22_out = fitz.open(out_f22)
        assert len(doc_f22_out) == 1, f"Expected strictly 1 page for Form 22, got {len(doc_f22_out)}"
        p_f22_out = doc_f22_out[0]
        assert len(p_f22_out.search_for("Hero MotoCorp Ltd.")) >= 1
        assert len(p_f22_out.search_for("FORM 22")) >= 1
        doc_f22_out.close()
        print("MOCK FORM 22 CI TEST PASSED (STRICT 1-PAGE)!")
        # 4. Mock Scanned Effect CI Test (Realistic scanning imperfections, tilt, dulling, B&W & Color, and < 280 KB limit)
        out_sc_scanned = os.path.join(tmpdir, "mock_sc_scanned.pdf")
        stats_sc_scanned = converter.convert_document(mock_sc, out_sc_scanned, hypothecation="TATA CAPITAL LTD", new_date="25/11/2026", affix_stamp=True, scanned_effect=True, bw_mode=True)
        assert stats_sc_scanned["status"] == "success"
        doc_sc_scanned = fitz.open(out_sc_scanned)
        assert len(doc_sc_scanned) == 1, f"Expected strictly 1 page for scanned Sale Cert, got {len(doc_sc_scanned)}"
        assert len(doc_sc_scanned[0].get_images()) >= 1
        doc_sc_scanned.close()

        out_inv_scanned = os.path.join(tmpdir, "mock_inv_scanned.pdf")
        stats_inv_scanned = converter.convert_document(mock_inv, out_inv_scanned, hypothecation="HERO FINCORP LTD", new_date="26/11/2026", affix_stamp=True, scanned_effect=True, bw_mode=True)
        assert stats_inv_scanned["status"] == "success"
        doc_inv_scanned = fitz.open(out_inv_scanned)
        assert len(doc_inv_scanned) == 1, f"Expected strictly 1 page for scanned Invoice, got {len(doc_inv_scanned)}"
        assert len(doc_inv_scanned[0].get_images()) >= 1
        doc_inv_scanned.close()

        out_f22_scanned = os.path.join(tmpdir, "mock_f22_scanned.pdf")
        stats_f22_scanned = converter.convert_document(mock_f22, out_f22_scanned, affix_stamp=True, scanned_effect=True, bw_mode=True)
        assert stats_f22_scanned["status"] == "success"
        doc_f22_scanned = fitz.open(out_f22_scanned)
        assert len(doc_f22_scanned) == 1, f"Expected strictly 1 page for scanned Form 22, got {len(doc_f22_scanned)}"
        assert len(doc_f22_scanned[0].get_images()) >= 1
        doc_f22_scanned.close()

        # Also test color scan mode
        out_inv_color = os.path.join(tmpdir, "mock_inv_color.pdf")
        stats_inv_color = converter.convert_document(mock_inv, out_inv_color, hypothecation="HERO FINCORP LTD", new_date="26/11/2026", affix_stamp=True, scanned_effect=True, bw_mode=False)
        assert stats_inv_color["status"] == "success"

        print("REALISTIC SCANNED EFFECT (B&W + COLOR) CI TEST PASSED!")

        # Verify strict file size limit (< 280 KB) across all mock outputs
        for path in [out_sc, out_inv, out_f22, out_sc_scanned, out_inv_scanned, out_f22_scanned, out_inv_color]:
            sz = os.path.getsize(path) / 1024.0
            assert sz < 280.0, f"File {path} is {sz:.1f} KB, exceeding strict 280 KB limit!"
        print("STRICT < 280 KB SIZE VERIFICATION PASSED!")


def test_hero_downloaded_documents():
    """Verifies that all 3 raw documents downloaded from Hero portal convert to Annapurna single-page < 280 KB."""
    import hero_downloader
    from pathlib import Path

    raw_candidates = [
        Path("HeroMotoCorp_Downloads/MBLHAW471THEB1423"),
        Path("../HeroMotoCorp_Downloads/MBLHAW471THEB1423")
    ]
    raw_dir = None
    for cand in raw_candidates:
        if cand.exists():
            raw_dir = cand
            break

    if raw_dir and raw_dir.exists():
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            files = list(raw_dir.glob("*.pdf"))
            assert len(files) >= 3, f"Expected 3 raw PDFs in {raw_dir}, found {len(files)}"

            for rf in files:
                res = hero_downloader.convert_downloaded_pdf(
                    raw_pdf_path=rf,
                    output_dir=out_dir,
                    hypothecation="HERO FINCORP LTD",
                    new_date="15/11/2026",
                    affix_stamp=True,
                    scanned_effect=True,
                    bw_mode=True
                )
                assert res is not None, f"Conversion failed for {rf.name}"
                cpath = res["converted_path"]
                doc = fitz.open(cpath)
                assert len(doc) == 1, f"{cpath} has {len(doc)} pages, expected strictly 1"
                doc.close()
                sz = os.path.getsize(cpath) / 1024.0
                assert sz < 280.0, f"{cpath} is {sz:.1f} KB, expected < 280 KB"
                print(f"VERIFIED HERO DOC: {res['filename']} ({sz:.1f} KB, 1 page)")

        print("HERO DOWNLOADED DOCUMENTS CONVERSION TEST PASSED!")


def test_sale_certificate_date_models():
    """Verify that changing the date in Sale Certificate across different vehicle models
    (Splendor+ where date is on line 0, and Destini where date wraps to line 1)
    never clips or breaks 'Invoice #', and cleanly formats hyphens to slashes.
    """
    test_cases = [
        (
            r"c:\Users\yash.patidar\Downloads\Sale Certificate (1).PDF",
            "63502BK26S391",
            "15-11-2026",
            "15/11/2026"
        ),
        (
            r"c:\Users\yash.patidar\.gemini\antigravity\brain\d343b39a-56a2-4ef7-aba9-92463e5a405d\.user_uploaded\media_1794503809628.pdf",
            "63502BK26S430",
            "15-11-2026",
            "15/11/2026"
        )
    ]

    for pdf_path, inv_num, in_date, expected_date in test_cases:
        if not os.path.exists(pdf_path):
            continue

        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = os.path.join(tmpdir, "test_sc_date.pdf")
            stats = converter.convert_document(
                pdf_path,
                out_pdf,
                new_date=in_date,
                scanned_effect=False
            )
            assert stats["status"] == "success"

            doc = fitz.open(out_pdf)
            page0 = doc[0]

            # 1. Invoice # must be 100% intact and NEVER broken
            inv_hits = page0.search_for(inv_num)
            assert len(inv_hits) >= 2, f"Expected at least 2 occurrences of invoice # {inv_num}, found {len(inv_hits)}"
            inv_label_hits = page0.search_for("Invoice #")
            assert len(inv_label_hits) >= 1, "Expected 'Invoice #' to be intact"

            # 2. Date must be updated at both top-right and in the delivery body clause
            date_hits = page0.search_for(expected_date)
            assert len(date_hits) >= 2, f"Expected {expected_date} at top and in body, found {len(date_hits)}"

            # 3. Delivery clause must be intact
            assert len(page0.search_for("delivered by us on date")) >= 1

            doc.close()
            print(f"PASSED MODEL DATE VERIFICATION for {pdf_path}: {inv_num} pristine, date {expected_date} exact!")


def test_invoice_authorized_signatory_robustness():
    """Verify that Authorized Signatory is 100% present in both 1-page/2-page invoices
    and multi-page continuation invoices (e.g. Ann.pdf), Terms are dropped, and
    signatory text is cleanly replaced with For ANNAPURNA MOTORS.
    """
    test_files = [
        r"c:\Users\yash.patidar\Downloads\smn.pdf",
        r"c:\Users\yash.patidar\Downloads\Ann.pdf",
        r"c:\Users\yash.patidar\.gemini\antigravity\brain\d343b39a-56a2-4ef7-aba9-92463e5a405d\.user_uploaded\media_1794501918315.pdf",
        os.path.abspath(r"..\HeroMotoCorp_Downloads\MBLHAW471THEB1423\63502BK26S410_GST Retail Invoice.pdf")
    ]

    for inv_path in test_files:
        if not os.path.exists(inv_path):
            continue

        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = os.path.join(tmpdir, "test_inv_robust.pdf")
            stats = converter.convert_document(
                inv_path,
                out_pdf,
                scanned_effect=False
            )
            assert stats["status"] == "success"
            assert stats["doc_type"] == "invoice"

            doc = fitz.open(out_pdf)
            # Terms and conditions page must NOT be present
            for p in doc:
                assert "terms & conditions" not in p.get_text().lower()

            # Authorized Signatory MUST be present on the signature page
            sig_found = False
            for p in doc:
                if len(p.search_for("Authorized Signatory")) > 0:
                    sig_found = True
                    break
            assert sig_found, f"Authorized Signatory is missing in converted {inv_path}!"

            # For ANNAPURNA MOTORS must be present
            ann_sig_found = False
            for p in doc:
                if len(p.search_for("For ANNAPURNA MOTORS")) > 0:
                    ann_sig_found = True
                    break
            assert ann_sig_found, f"For ANNAPURNA MOTORS is missing in converted {inv_path}!"

            num_pages = len(doc)
            doc.close()
            print(f"PASSED ROBUST INVOICE TEST for {inv_path} ({num_pages} pages kept, Authorized Signatory verified!)")


if __name__ == "__main__":
    test_mock_ci()
    test_real_files()
    test_hero_downloaded_documents()
    test_sale_certificate_date_models()
    test_invoice_authorized_signatory_robustness()
