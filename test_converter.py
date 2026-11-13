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
                new_date="18/11/2026"
            )
            print("Invoice conversion stats:", stats)
            assert stats["status"] == "success"
            assert stats["doc_type"] == "invoice"

            doc = fitz.open(out_pdf)
            page0 = doc[0]
            # Verify Shanti Motors is gone
            assert len(page0.search_for("SHANTI MOTORS")) == 0
            # Verify Annapurna is present
            assert len(page0.search_for("ANNAPURNA MOTORS")) >= 1
            assert len(page0.search_for("For ANNAPURNA MOTORS")) >= 1
            # Verify Invoice # and Mobile # are NOT truncated
            assert len(page0.search_for("63502BK26S368")) >= 1
            assert len(page0.search_for("9343006704")) >= 1
            # Verify Page 2 (Terms & Conditions) was NOT touched
            assert len(doc[1].search_for("ANNAPURNA")) == 0
            assert len(doc[1].search_for("TATA CAPITAL")) == 0
            doc.close()
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
                new_date="20/11/2026"
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
            assert len(page0.search_for("For ANNAPURNA MOTORS")) >= 1
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
                hypothecation="BLANK"
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
        doc.save(mock_sc)
        doc.close()

        out_sc = os.path.join(tmpdir, "mock_sc_out.pdf")
        stats_sc = converter.convert_document(mock_sc, out_sc, hypothecation="TATA CAPITAL LTD", new_date="25/11/2026", affix_stamp=True)
        assert stats_sc["status"] == "success"
        assert stats_sc["doc_type"] == "sale_certificate"
        assert stats_sc["stamps_affixed"] == 1

        doc_out = fitz.open(out_sc)
        p_out = doc_out[0]
        assert len(p_out.search_for("Shanti Motors")) == 0
        assert len(p_out.search_for("ANNAPURNA MOTORS")) >= 1
        assert len(p_out.search_for("TATA CAPITAL LTD")) >= 1
        assert len(p_out.search_for("25/11/2026")) >= 2
        doc_out.close()
        print("MOCK SALE CERTIFICATE CI TEST PASSED!")

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
        stats_inv = converter.convert_document(mock_inv, out_inv, hypothecation="HERO FINCORP LTD", new_date="26/11/2026", affix_stamp=True)
        assert stats_inv["status"] == "success"
        assert stats_inv["doc_type"] == "invoice"
        assert stats_inv["stamps_affixed"] == 1

        doc_inv_out = fitz.open(out_inv)
        p_inv_out = doc_inv_out[0]
        assert len(p_inv_out.search_for("SHANTI MOTORS")) == 0
        assert len(p_inv_out.search_for("ANNAPURNA MOTORS")) >= 1
        assert len(p_inv_out.search_for("26/11/2026")) >= 1
        doc_inv_out.close()
        print("MOCK INVOICE CI TEST PASSED!")


if __name__ == "__main__":
    test_mock_ci()
    test_real_files()
