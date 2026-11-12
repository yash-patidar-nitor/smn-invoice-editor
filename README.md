# Hero Invoice Converter (SMN Invoice Editor)

A clean, modern, and simple desktop application and batch processing tool to convert **Shanti Motors** invoices into **Annapurna Motors** invoices (and vice-versa).

Built for **Hero MotoCorp Ltd.** tax invoice PDFs, using PyMuPDF for vector redaction and typographic alignment.

---

## ✨ Features

- **High-Fidelity PDF Conversion**: Redacts original dealership header block and signatory text, replacing them with crisp vector text matched to the exact template layout.
- **Clean & Simple UI**: Built with a modern Windows UI theme (`clam` + `Segoe UI`), card layouts, progress bar, real-time log box, and one-click actions.
- **Batch & File Processing**: Select individual PDF files or an entire folder of invoices.
- **Bidirectional Support**:
  - `Shanti Motors ➔ Annapurna Motors` (Default mode)
  - `Annapurna Motors ➔ Shanti Motors` (Reverse mode)
- **One-Click Actions**:
  - Direct button to open the output destination folder in File Explorer.
  - Quick button to view/open the latest converted PDF in your system PDF viewer.
- **Command-Line Interface (CLI)**: Automate conversions via script or terminal.
- **One-Click Windows Launcher**: Double-click `Launch_Invoice_Converter.bat` to launch instantly.

---

## 🏢 Dealership Details

### Annapurna Motors (Output Preset)
- **Dealer Name**: `ANNAPURNA MOTORS`
- **Address Line 1**: `Khasra 193/1  Ward 15 Alirajpur Road`
- **Address Line 2**: `KUKSHI DHAR MADHYA PRADESH 454331 State Code: 23 Contact #     9755820013`
- **Authorization**: `Authorized Dealer: Hero MotoCorp Ltd.`
- **GSTIN & PAN**: `GSTIN #: 23AFTPG6974R1ZE PAN# AFTPG6974R`
- **Signatory**: `For ANNAPURNA MOTORS`

### Shanti Motors (Source Preset)
- **Dealer Name**: `M/S.SHANTI MOTORS`
- **Address Line 1**: `NEAR NEW BUS STAND, PUNARVAS NISARPUR`
- **Address Line 2**: `KUKSHI DHAR MADHYA PRADESH 454335 State Code: 23 Contact #     9131076286`
- **Authorization**: `Authorized Representative of Dealer: Hero MotoCorp Ltd.`
- **GSTIN**: `GSTIN #: 23AQMPP0120E1ZE`
- **Signatory**: `For M/S.SHANTI MOTORS`

---

## 🚀 Quick Start

### 1. Installation
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Launch Desktop GUI
Double-click `Launch_Invoice_Converter.bat` or run:
```bash
python app.py
```

### 3. Command Line (CLI) Batch Conversion
Convert a single invoice:
```bash
python converter.py --input path/to/shanti_invoice.pdf --output path/to/annapurna_invoice.pdf
```

Batch convert an entire directory:
```bash
python converter.py --input ./input_invoices --output ./output_invoices --direction shanti_to_annapurna
```

---

## 🧪 Running Tests
Run the included test suite to verify conversion and layout integrity:
```bash
python test_converter.py
```

---

## 📁 Repository Structure

```
smn-invoice-editor/
├── app.py                         # Clean Desktop GUI application
├── converter.py                   # Core PDF redaction and conversion engine
├── test_converter.py              # Automated verification test suite
├── Launch_Invoice_Converter.bat   # Windows one-click desktop launcher
├── requirements.txt               # Dependencies (PyMuPDF)
├── README.md                      # Documentation
└── .gitignore                     # Git ignore rules
```
