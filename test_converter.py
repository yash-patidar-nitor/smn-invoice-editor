"""
Test suite for Invoice Converter.
Verifies conversion, redaction, text placement, and batch mode.
Works self-contained across any CI environment (including GitHub Actions).
"""

import os
import tempfile
import fitz
import converter


def create_mock_shanti_pdf(pdf_path: str):
    """Generate a clean mock Hero invoice with Shanti Motors details."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # Standard A4

    # Header block
    page.insert_text((28.35, 120.5), "M/S.SHANTI MOTORS", fontsize=9.0, fontname="helv")
    page.insert_text((28.35, 131.0), "NEAR NEW BUS STAND, PUNARVAS NISARPUR", fontsize=9.0, fontname="helv")
    page.insert_text((28.35, 142.0), "KUKSHI DHAR MADHYA PRADESH 454335 State Code: 23 Contact #     9131076286", fontsize=9.0, fontname="helv")
    page.insert_text((28.35, 153.0), "Authorized Representative of Dealer: Hero MotoCorp Ltd.", fontsize=9.0, fontname="helv")
    page.insert_text((28.35, 164.0), "GSTIN #: 23AQMPP0120E1ZE", fontsize=9.0, fontname="helv")

    # Body sample
    page.insert_text((28.35, 250.0), "TAX INVOICE", fontsize=12.0, fontname="helv")
    page.insert_text((28.35, 280.0), "Customer: Test Customer", fontsize=9.0, fontname="helv")

    # Footer block
    page.insert_text((467.5, 636.5), "For M/S.SHANTI MOTORS", fontsize=9.0, fontname="helv")
    page.insert_text((486.0, 683.0), "Authorized Signatory", fontsize=9.0, fontname="helv")

    doc.save(pdf_path)
    doc.close()


def test_conversion():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_pdf = os.path.join(tmpdir, "test_input.pdf")
        output_pdf = os.path.join(tmpdir, "test_output.pdf")

        create_mock_shanti_pdf(input_pdf)
        assert os.path.exists(input_pdf), "Failed to create mock PDF"

        # 1. Convert Shanti -> Annapurna
        res = converter.convert_shanti_to_annapurna(input_pdf, output_pdf)
        print("Conversion result:", res)
        assert res["status"] == "success", f"Conversion failed: {res}"
        assert res["headers_replaced"] >= 1, "Header was not replaced"
        assert res["footers_replaced"] >= 1, "Footer was not replaced"

        # 2. Inspect output PDF
        doc = fitz.open(output_pdf)
        page0 = doc[0]

        # Verify Shanti Motors is completely redacted
        shanti_hits = page0.search_for("SHANTI MOTORS")
        assert len(shanti_hits) == 0, f"Shanti Motors remains: {shanti_hits}"

        # Verify Annapurna Motors is present in both header and footer
        ann_hits = page0.search_for("ANNAPURNA MOTORS")
        assert len(ann_hits) >= 2, f"Expected at least 2 Annapurna hits, got {len(ann_hits)}"
        doc.close()

        # 3. Test Reverse Mode: Annapurna -> Shanti
        rev_output = os.path.join(tmpdir, "test_reverse.pdf")
        res_rev = converter.convert_annapurna_to_shanti(output_pdf, rev_output)
        assert res_rev["status"] == "success", f"Reverse conversion failed: {res_rev}"

        doc_rev = fitz.open(rev_output)
        rev_page0 = doc_rev[0]
        assert len(rev_page0.search_for("ANNAPURNA MOTORS")) == 0, "Annapurna Motors should be redacted in reverse"
        assert len(rev_page0.search_for("SHANTI MOTORS")) >= 1, "Shanti Motors should be restored in reverse"
        doc_rev.close()

        # 4. Test Batch Processing
        batch_out_dir = os.path.join(tmpdir, "batch_out")
        batch_res = converter.batch_convert(tmpdir, batch_out_dir, direction="shanti_to_annapurna")
        assert len(batch_res) >= 1, "Batch conversion returned no results"

    print("ALL TESTS PASSED: Standalone test suite verified successfully!")


def test_real_sample_if_present():
    sample_path = r"c:\Users\yash.patidar\Downloads\smn.pdf"
    if os.path.exists(sample_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_pdf = os.path.join(tmpdir, "annapurna_smn_real.pdf")
            res = converter.convert_shanti_to_annapurna(sample_path, out_pdf)
            assert res["status"] == "success"
            doc = fitz.open(out_pdf)
            assert len(doc[0].search_for("SHANTI MOTORS")) == 0
            doc.close()
            print("REAL SAMPLE TEST PASSED: Verified on smn.pdf!")


if __name__ == "__main__":
    test_conversion()
    test_real_sample_if_present()
