# Hero Invoice Converter (SMN Invoice Editor)

A clean, modern, and simple **Web Application** (and Desktop / CLI tool) to convert **Shanti Motors** invoices into **Annapurna Motors** invoices (and vice-versa).

Built for **Hero MotoCorp Ltd.** tax invoice PDFs, using high-precision vector redaction and typographic alignment.

---

## 🌐 Live Web App (GitHub Pages)

You can run the web app directly in your browser with **zero installation**:

👉 **[Launch Live Web App](https://yash-patidar-nitor.github.io/smn-invoice-editor/)** *(Active upon GitHub Pages enablement)*

- **100% Client-Side Privacy**: Runs locally in your browser via WebAssembly/pdf-lib. Your PDFs never leave your machine.
- **Drag & Drop**: Select single or batch PDF invoices.
- **Instant In-Browser Preview**: View before and after invoice previews.
- **1-Click Batch Download**: Download converted invoices individually or all together as a `.zip`.

---

## 💻 Run Web App Locally (Python / Flask)

You can also run the full-featured Python Flask web server locally:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the web server
python server.py
```
Or simply double-click **`Launch_Web_App.bat`** on Windows. The app opens automatically at:
`http://localhost:5000`

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

## ⚡ Command Line (CLI) Batch Conversion

Convert a single invoice:
```bash
python converter.py --input path/to/shanti_invoice.pdf --output path/to/annapurna_invoice.pdf
```

Batch convert an entire directory:
```bash
python converter.py --input ./input_invoices --output ./output_invoices --direction shanti_to_annapurna
```

---

## 🖥 Windows Desktop GUI

A standalone Windows desktop app is also available:
- Double-click **`Launch_Invoice_Converter.bat`** or run:
  ```bash
  python app.py
  ```

---

## 🤖 GitHub Actions CI/CD Workflows

The repository includes pre-configured GitHub Actions workflows in `.github/workflows/`:

1. **GitHub Pages Deployment (`deploy-pages.yml`)**:
   - Automatically builds and deploys the live web app to GitHub Pages on every push to `main`.
2. **CI Test Suite (`ci.yml`)**:
   - Tests across Linux and Windows runners on Python 3.10, 3.11, and 3.12.
3. **Automated Windows Build (`build-windows-exe.yml`)**:
   - Packages the app into a standalone portable `HeroInvoiceConverter.exe` using PyInstaller.

---

## 🧪 Running Tests
Run the automated test suite to verify conversion and layout integrity:
```bash
python test_converter.py
```

---

## 📁 Repository Structure

```
smn-invoice-editor/
├── .github/
│   └── workflows/
│       ├── deploy-pages.yml           # Deploys Web App to GitHub Pages
│       ├── ci.yml                     # Automated multi-OS test matrix
│       └── build-windows-exe.yml      # PyInstaller standalone Windows .exe build
├── index.html                         # Client-side Web App for GitHub Pages
├── server.py                          # Flask Web Server
├── Launch_Web_App.bat                 # 1-Click launcher for local web app
├── Dockerfile                         # Container deployment file
├── app.py                             # Desktop GUI application
├── Launch_Invoice_Converter.bat       # 1-Click launcher for desktop GUI
├── converter.py                       # Core PDF redaction and conversion engine
├── test_converter.py                  # Automated verification test suite
├── requirements.txt                   # Dependencies (PyMuPDF, Flask)
├── README.md                          # Documentation
└── .gitignore                         # Git ignore rules
```
