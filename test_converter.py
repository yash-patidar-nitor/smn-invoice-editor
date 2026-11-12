"""
Test suite for Invoice Converter.
"""
import os
import fitz
import converter

def test_shanti_to_annapurna():
    sample_path = r"c:\Users\yash.patidar\Downloads\smn.pdf"
    if not os.path.exists(sample_path):
        print(f"Skipping test: {sample_path} not found")
        return

    output_path = r"c:\Users\yash.patidar\Downloads\annapurna_smn_test.pdf"
    res = converter.convert_shanti_to_annapurna(sample_path, output_path)
    print("Conversion result:", res)
    assert res["status"] == "success", f"Failed with result: {res}"
    assert res["headers_replaced"] >= 1, "Header not replaced"
    assert res["footers_replaced"] >= 1, "Footer not replaced"
    assert os.path.exists(output_path), "Output file does not exist"
    
    doc = fitz.open(output_path)
    page0 = doc[0]
    # Check shanti motors is gone
    shanti_hits = page0.search_for("SHANTI MOTORS")
    assert len(shanti_hits) == 0, f"Found remaining Shanti Motors hits: {shanti_hits}"
    
    # Check Annapurna is present in header and footer
    ann_header = page0.search_for("ANNAPURNA MOTORS")
    assert len(ann_header) >= 1, "Annapurna Motors text not found in converted PDF"
    
    footer_ann = page0.search_for("For ANNAPURNA MOTORS")
    assert len(footer_ann) >= 1, "'For ANNAPURNA MOTORS' not found in footer"
    doc.close()
    
    print("TASKS PASSED: Shanti Motors -> Annapurna Motors conversion verified successfully!")

if __name__ == "__main__":
    test_shanti_to_annapurna()
