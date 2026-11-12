# Hero Invoice & Sale Certificate Converter (SMN Editor)

A clean, modern, and simple **Web Application** (and Desktop / CLI tool) to convert **Shanti Motors** Tax Invoices and Form 21 Sale Certificates into official **Annapurna Motors** format.

Built for **Hero MotoCorp Ltd.** documents, using high-precision vector redaction, typography matching, and right-aligned signatory layout.

---

## ✨ Features & Capabilities

- **Automatic Document Detection**:
  - Automatically identifies whether an uploaded PDF is a **Tax Invoice** or a **Form 21 Sale Certificate**.
  - Applies template-specific headers, line heights, and footer coordinates.
- **Customizable Hypothecation Bank**:
  - Dropdown options:
    - `Keep Original (No Change)`
    - `HERO FINCORP LTD`
    - `TATA CAPITAL LTD`
    - `AASTHA SAKH SAHKARITA`
    - `Leave Blank (Cash / None)`
  - Accurately updates or blanks out the finance hypothecation field across Invoices and Sale Certificates.
- **Customizable Date**:
  - Option to update document dates (`DD/MM/YYYY`).
  - Updates date at top-right, and in the Sale Certificate delivery clause.
- **Clean File Naming**:
  - Appends the **`_smn`** suffix to distinguish converted files from originals (e.g. `invoice_smn.pdf`, `Sale_Certificate_smn.pdf`).
- **Batch Processing & ZIP Download**:
  - Drag & drop multiple invoices and sale certificates together.
  - Download converted files individually or all at once in a single `.zip` archive.

---

## 🚀 Recommended: Run Web App Locally (Zero Lag, Fast PyMuPDF Engine)

The fastest and most reliable way to use the Web App is via the Python server:

1. Double-click **`Launch_Web_App.bat`** (or run `python server.py`).
2. Your browser opens automatically at **`http://localhost:5000`**.
3. **Features**:
   - Converts both Tax Invoices & Form 21 Sale Certificates in **under 0.2 seconds** (<200ms) with zero browser lag.
   - 100% native file picker and drag-and-drop.
   - Hypothecation selector, custom date input, live PDF preview, and 1-click ZIP download.

---

## 🌐 Live Web App (GitHub Pages)

Run directly in your browser with **zero installation**:

👉 **[Launch Live Web App](https://yash-patidar-nitor.github.io/smn-invoice-editor/)** *(Active upon GitHub Pages enablement)*

- **100% Client-Side Privacy**: Runs locally in your browser using lightweight `pdf-lib`. Your documents never leave your computer.
- **Drag & Drop**: Drop single or batch PDF documents.
- **Interactive Preview**: In-browser modal preview of converted documents.

---

## 🖥 Windows Desktop GUI (Optional)

A standalone Windows desktop application is also included:
- Double-click **`Launch_Invoice_Converter.bat`** or run:
  ```bash
  python app.py
  ```

---

## ⚡ Command Line (CLI) Batch Usage

Convert a single document:
```bash
python converter.py --input path/to/invoice.pdf --output path/to/invoice_smn.pdf --hypo "TATA CAPITAL LTD" --date "15/11/2026"
```

Batch convert an entire directory:
```bash
python converter.py --input ./input_folder --output ./output_folder --hypo "AASTHA SAKH SAHKARITA"
```

---

## 🏢 Dealership Details

### Annapurna Motors (Output Template)
- **Dealer Name**: `ANNAPURNA MOTORS`
- **Address Line 1**: `Khasra 193/1  Ward 15 Alirajpur Road`
- **Address Line 2**: `KUKSHI DHAR MADHYA PRADESH 454331 State Code: 23 Contact #     9755820013`
- **Authorization**: `Authorized Dealer: Hero MotoCorp Ltd.`
- **GSTIN & PAN**: `GSTIN #: 23AFTPG6974R1ZE PAN# AFTPG6974R` *(on Tax Invoices)*
- **Signatory**: `For ANNAPURNA MOTORS`

---

## 🤖 GitHub Actions CI/CD Workflows

Pre-configured workflows in `.github/workflows/`:
1. **GitHub Pages Deployment (`deploy-pages.yml`)**: Deploys web app to GitHub Pages on every push to `main`.
2. **CI Test Suite (`ci.yml`)**: Multi-OS & multi-Python test matrix verifying conversions.
3. **Automated Windows Build (`build-windows-exe.yml`)**: Compiles standalone portable `.exe`.

---

## 🧪 Running Tests
Run the test suite verifying invoices, sale certificates, hypothecation, and dates:
```bash
python test_converter.py
```
