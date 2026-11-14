"""
Hero Invoice & Sale Certificate Converter - Desktop Application
Clean, modern desktop interface for converting Shanti Motors
Tax Invoices, Sale Certificates, and Form 22 to Annapurna Motors format.

Features:
- Direct Hero Portal Auto-Download & Convert (Playwright automation)
- Configurable User ID & Password with Show/Hide toggle
- Local PDF Batch & Single file conversion
- Strict single-page output (< 280 KB)
- Realistic B&W scanned laser print mode & authentic dealer rubber stamp
"""

import os
import sys
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Ensure current dir is in sys.path
script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

import converter
import hero_downloader


class ModernInvoiceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hero MotoCorp Document Converter - Annapurna Motors")
        self.geometry("780x880")
        self.minsize(700, 780)

        self.configure(bg="#F8FAFC")
        self.setup_styles()

        # Shared State
        self.output_dir = os.path.abspath("output_invoices")
        self.hypo_var = tk.StringVar(value="Keep Original (No Change)")
        self.date_var = tk.StringVar(value="")
        self.stamp_var = tk.BooleanVar(value=True)
        self.scanned_var = tk.BooleanVar(value=True)
        self.bw_var = tk.BooleanVar(value=True)

        # Hero Portal State
        self.hero_user_var = tk.StringVar(value=hero_downloader.DEFAULT_USERNAME)
        self.hero_pass_var = tk.StringVar(value=hero_downloader.DEFAULT_PASSWORD)
        self.hero_show_pass_var = tk.BooleanVar(value=False)
        self.hero_vin_var = tk.StringVar(value="MBLHAW471THEB1423")
        self.hero_headless_var = tk.BooleanVar(value=True)
        self.hero_bulk_vins = []

        # Local Files State
        self.input_files = []
        self.last_converted_file = None

        self.build_ui()

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        font_family = "Segoe UI" if sys.platform == "win32" else "Helvetica"
        self.font_title = (font_family, 15, "bold")
        self.font_sub = (font_family, 9)
        self.font_heading = (font_family, 10, "bold")
        self.font_bold = (font_family, 9, "bold")
        self.font_regular = (font_family, 9)

        style.configure("TFrame", background="#F8FAFC")
        style.configure("Card.TFrame", background="#FFFFFF", relief="solid", borderwidth=1)
        style.configure("TLabel", background="#F8FAFC", foreground="#0F172A", font=self.font_regular)
        style.configure("Card.TLabel", background="#FFFFFF", foreground="#0F172A", font=self.font_regular)
        style.configure("CardHeading.TLabel", background="#FFFFFF", foreground="#0F172A", font=self.font_heading)
        style.configure("Muted.TLabel", background="#FFFFFF", foreground="#64748B", font=self.font_sub)

        style.configure("TNotebook", background="#F8FAFC", borderwidth=0)
        style.configure("TNotebook.Tab", background="#E2E8F0", foreground="#475569", padding=[16, 8], font=self.font_bold)
        style.map("TNotebook.Tab",
                  background=[("selected", "#2563EB")],
                  foreground=[("selected", "#FFFFFF")])

        style.configure("Primary.TButton", background="#2563EB", foreground="#FFFFFF", font=self.font_bold, borderwidth=0, padding=8)
        style.map("Primary.TButton",
                  background=[("active", "#1D4ED8"), ("disabled", "#93C5FD")],
                  foreground=[("disabled", "#FFFFFF")])

        style.configure("Secondary.TButton", background="#E2E8F0", foreground="#1E293B", font=self.font_regular, borderwidth=0, padding=6)
        style.map("Secondary.TButton", background=[("active", "#CBD5E1")])

        style.configure("Success.TButton", background="#16A34A", foreground="#FFFFFF", font=self.font_bold, borderwidth=0, padding=8)
        style.map("Success.TButton", background=[("active", "#15803D")])

        style.configure("TCheckbutton", background="#FFFFFF", font=self.font_regular)
        style.configure("TProgressbar", thickness=10, troughcolor="#E2E8F0", background="#2563EB")

    def build_ui(self):
        main_frame = ttk.Frame(self, padding="18 12 18 12")
        main_frame.pack(fill="both", expand=True)

        # Header Title Card
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        lbl_badge = tk.Label(header_frame, text="Shanti Motors ➔ Annapurna Motors", font=(self.font_sub[0], 8, "bold"), bg="#DBEAFE", fg="#2563EB", padx=8, pady=2)
        lbl_badge.pack(anchor="w", pady=(0, 4))

        lbl_title = tk.Label(header_frame, text="Hero Document Converter & Auto-Downloader", font=self.font_title, bg="#F8FAFC", fg="#0F172A")
        lbl_title.pack(anchor="w")

        lbl_desc = tk.Label(header_frame, text="Download directly from Siebel Portal or convert local Invoices, Form 21 Sale Certificates & Form 22", font=self.font_sub, bg="#F8FAFC", fg="#64748B")
        lbl_desc.pack(anchor="w")

        # Global Options Card (Hypothecation, Date, Stamp, Scanned B&W)
        opt_card = self.create_card(main_frame, "1. Conversion Settings")
        opt_inner = ttk.Frame(opt_card, style="Card.TFrame")
        opt_inner.pack(fill="x", padx=12, pady=(4, 10))

        grid_frame = ttk.Frame(opt_inner, style="Card.TFrame")
        grid_frame.pack(fill="x")

        # Column 1: Hypothecation
        col1 = ttk.Frame(grid_frame, style="Card.TFrame")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(col1, text="Hypothecation Financier:", style="Card.TLabel", font=self.font_bold).pack(anchor="w", pady=(0, 2))

        hypo_options = [
            "Keep Original (No Change)",
            "HERO FINCORP LTD",
            "TATA CAPITAL LTD",
            "AASTHA SAKH SAHKARITA",
            "Leave Blank (Cash / None)"
        ]
        self.hypo_combo = ttk.Combobox(col1, textvariable=self.hypo_var, values=hypo_options, state="readonly", font=self.font_regular)
        self.hypo_combo.pack(fill="x")

        # Column 2: Date
        col2 = ttk.Frame(grid_frame, style="Card.TFrame")
        col2.pack(side="right", fill="x", expand=True, padx=(8, 0))
        ttk.Label(col2, text="Change Date (DD/MM/YYYY):", style="Card.TLabel", font=self.font_bold).pack(anchor="w", pady=(0, 2))
        self.date_entry = ttk.Entry(col2, textvariable=self.date_var, font=self.font_regular)
        self.date_entry.pack(fill="x")

        # Checkboxes Row
        chk_row = ttk.Frame(opt_inner, style="Card.TFrame")
        chk_row.pack(fill="x", pady=(10, 2))
        ttk.Checkbutton(chk_row, text="✍️ Dealer Stamp & Signature", variable=self.stamp_var, style="TCheckbutton").pack(side="left", padx=(0, 14))
        ttk.Checkbutton(chk_row, text="📄 Realistic Scanned Look", variable=self.scanned_var, style="TCheckbutton").pack(side="left", padx=(0, 14))
        ttk.Checkbutton(chk_row, text="🖨️ Laser B&W Mode", variable=self.bw_var, style="TCheckbutton").pack(side="left")

        # Primary Tabs: Hero Portal Automation vs Local Files
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(6, 8))

        # Tab 1: Hero Portal Automation
        tab_hero = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(tab_hero, text="⚡ Hero Portal Direct Download & Convert")
        self.build_hero_tab(tab_hero)

        # Tab 2: Local Files Converter
        tab_local = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(tab_local, text="📁 Local PDF Files Converter")
        self.build_local_tab(tab_local)

        # Shared Output & Progress Section at bottom
        self.build_bottom_section(main_frame)

    def create_card(self, parent, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=4)
        card.pack(fill="x", pady=(0, 8))
        title_lbl = ttk.Label(card, text=title, style="CardHeading.TLabel")
        title_lbl.pack(anchor="w", padx=12, pady=(6, 2))
        return card

    # ─── TAB 1: HERO PORTAL ───────────────────────────────────────────────────
    def build_hero_tab(self, parent):
        container = ttk.Frame(parent, padding="8 10 8 10")
        container.pack(fill="both", expand=True)

        # Credentials Card
        cred_card = self.create_card(container, "Hero MotoCorp Portal Credentials")
        cred_inner = ttk.Frame(cred_card, style="Card.TFrame")
        cred_inner.pack(fill="x", padx=12, pady=(4, 8))

        cred_grid = ttk.Frame(cred_inner, style="Card.TFrame")
        cred_grid.pack(fill="x")

        # User ID
        u_col = ttk.Frame(cred_grid, style="Card.TFrame")
        u_col.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(u_col, text="Portal User ID / Username:", style="Card.TLabel", font=self.font_bold).pack(anchor="w", pady=(0, 2))
        self.entry_user = ttk.Entry(u_col, textvariable=self.hero_user_var, font=self.font_regular)
        self.entry_user.pack(fill="x")

        # Password
        p_col = ttk.Frame(cred_grid, style="Card.TFrame")
        p_col.pack(side="right", fill="x", expand=True, padx=(8, 0))
        ttk.Label(p_col, text="Portal Password:", style="Card.TLabel", font=self.font_bold).pack(anchor="w", pady=(0, 2))
        self.entry_pass = ttk.Entry(p_col, textvariable=self.hero_pass_var, show="*", font=self.font_regular)
        self.entry_pass.pack(fill="x")

        pass_opt_row = ttk.Frame(cred_inner, style="Card.TFrame")
        pass_opt_row.pack(fill="x", pady=(6, 0))
        ttk.Checkbutton(pass_opt_row, text="Show Password", variable=self.hero_show_pass_var,
                        command=self.toggle_password_visibility, style="TCheckbutton").pack(side="left")
        ttk.Checkbutton(pass_opt_row, text="Run Silently (Headless Browser)", variable=self.hero_headless_var,
                        style="TCheckbutton").pack(side="right")

        # VIN Selection Card
        vin_card = self.create_card(container, "Target Vehicle Identification Number (VIN / Chassis)")
        vin_inner = ttk.Frame(vin_card, style="Card.TFrame")
        vin_inner.pack(fill="x", padx=12, pady=(4, 8))

        vin_row = ttk.Frame(vin_inner, style="Card.TFrame")
        vin_row.pack(fill="x")
        ttk.Label(vin_row, text="Single VIN Number:", style="Card.TLabel", font=self.font_bold).pack(side="left", padx=(0, 8))
        self.entry_vin = ttk.Entry(vin_row, textvariable=self.hero_vin_var, font=self.font_bold)
        self.entry_vin.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_load_vins = ttk.Button(vin_row, text="📂 Load vin_list.txt", style="Secondary.TButton", command=self.load_vin_file)
        btn_load_vins.pack(side="right")

        self.lbl_vin_info = ttk.Label(vin_inner, text="Downloads 3 files: 1. GST Retail Invoice, 2. Sale Certificate, 3. Form 22", style="Muted.TLabel")
        self.lbl_vin_info.pack(anchor="w", pady=(4, 2))

        # Hero Action Button
        self.btn_hero_fetch = ttk.Button(
            container,
            text="🚀 Fetch 3 Documents from Hero Portal & Convert to Annapurna Motors",
            style="Primary.TButton",
            command=self.start_hero_automation
        )
        self.btn_hero_fetch.pack(fill="x", pady=(6, 4))

    def toggle_password_visibility(self):
        if self.hero_show_pass_var.get():
            self.entry_pass.config(show="")
        else:
            self.entry_pass.config(show="*")

    def load_vin_file(self):
        filename = filedialog.askopenfilename(
            title="Select VIN List File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    lines = [ln.strip().upper() for ln in f if ln.strip() and not ln.startswith("#")]
                if lines:
                    self.hero_bulk_vins = lines
                    self.entry_vin.delete(0, tk.END)
                    self.entry_vin.insert(0, lines[0])
                    self.lbl_vin_info.config(
                        text=f"Loaded {len(lines)} VIN(s) from {os.path.basename(filename)} (Active first VIN: {lines[0]})",
                        foreground="#2563EB"
                    )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    # ─── TAB 2: LOCAL FILES ───────────────────────────────────────────────────
    def build_local_tab(self, parent):
        container = ttk.Frame(parent, padding="8 10 8 10")
        container.pack(fill="both", expand=True)

        input_card = self.create_card(container, "Select Local Documents to Convert")
        btn_box = ttk.Frame(input_card, style="Card.TFrame")
        btn_box.pack(fill="x", padx=12, pady=6)

        btn_files = ttk.Button(btn_box, text="📁 Select PDF Files", style="Secondary.TButton", command=self.choose_files)
        btn_files.pack(side="left", padx=(0, 8))

        btn_dir = ttk.Button(btn_box, text="📂 Select Folder", style="Secondary.TButton", command=self.choose_folder)
        btn_dir.pack(side="left", padx=(0, 8))

        btn_clear = ttk.Button(btn_box, text="✖ Clear List", style="Secondary.TButton", command=self.clear_files)
        btn_clear.pack(side="right")

        self.file_listbox = tk.Listbox(input_card, height=4, selectmode="extended",
                                       bg="#F1F5F9", fg="#1E293B", relief="flat",
                                       highlightthickness=1, highlightbackground="#E2E8F0",
                                       font=self.font_regular)
        self.file_listbox.pack(fill="x", padx=12, pady=(2, 6))

        self.lbl_file_count = ttk.Label(input_card, text="No local files selected yet", style="Muted.TLabel")
        self.lbl_file_count.pack(anchor="w", padx=12, pady=(0, 10))

        self.btn_convert_local = ttk.Button(
            container,
            text="⚡ Convert Local Files to Annapurna Motors",
            style="Primary.TButton",
            command=self.start_local_conversion
        )
        self.btn_convert_local.pack(fill="x", pady=(6, 4))

    # ─── BOTTOM SECTION: DESTINATION, PROGRESS & LOG ──────────────────────────
    def build_bottom_section(self, parent):
        # Output Destination Card
        out_card = self.create_card(parent, "Output Destination")
        out_inner = ttk.Frame(out_card, style="Card.TFrame")
        out_inner.pack(fill="x", padx=12, pady=(4, 6))

        self.out_entry = ttk.Entry(out_inner, font=self.font_regular)
        self.out_entry.insert(0, self.output_dir)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_out = ttk.Button(out_inner, text="Browse...", style="Secondary.TButton", command=self.choose_output_dir)
        btn_out.pack(side="left", padx=(0, 6))

        btn_open_out = ttk.Button(out_inner, text="📂 Open Folder", style="Secondary.TButton", command=self.open_output_dir)
        btn_open_out.pack(side="left")

        # Progress & Console Log Card
        prog_card = self.create_card(parent, "Execution Status & Log")
        prog_inner = ttk.Frame(prog_card, style="Card.TFrame")
        prog_inner.pack(fill="both", expand=True, padx=12, pady=(4, 6))

        self.prog_var = tk.DoubleVar(value=0)
        self.prog_bar = ttk.Progressbar(prog_inner, variable=self.prog_var, maximum=100)
        self.prog_bar.pack(fill="x", pady=(0, 4))

        self.lbl_status = ttk.Label(prog_inner, text="Ready.", style="Card.TLabel", font=self.font_bold)
        self.lbl_status.pack(anchor="w", pady=(0, 4))

        self.log_text = tk.Text(prog_inner, height=6, bg="#0F172A", fg="#F8FAFC", relief="flat", font=("Consolas", 8))
        self.log_text.pack(fill="both", expand=True)

        # Action bar
        act_box = ttk.Frame(parent)
        act_box.pack(fill="x", pady=(6, 0))

        self.btn_open_latest = ttk.Button(act_box, text="👁 Open Converted File", style="Success.TButton", command=self.open_latest_pdf, state="disabled")
        self.btn_open_latest.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_open_folder2 = ttk.Button(act_box, text="📂 Open Output Folder", style="Secondary.TButton", command=self.open_output_dir)
        btn_open_folder2.pack(side="right", padx=(6, 0))

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def choose_output_dir(self):
        dir_selected = filedialog.askdirectory(title="Select Output Directory")
        if dir_selected:
            self.output_dir = dir_selected
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, dir_selected)

    def open_output_dir(self):
        out_p = self.out_entry.get().strip()
        os.makedirs(out_p, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(out_p)
        elif sys.platform == "darwin":
            subprocess.run(["open", out_p])
        else:
            subprocess.run(["xdg-open", out_p])

    def open_latest_pdf(self):
        if self.last_converted_file and os.path.exists(self.last_converted_file):
            if sys.platform == "win32":
                os.startfile(self.last_converted_file)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.last_converted_file])
            else:
                subprocess.run(["xdg-open", self.last_converted_file])

    # ─── HERO PORTAL AUTOMATION WORKER ────────────────────────────────────────
    def start_hero_automation(self):
        username = self.hero_user_var.get().strip()
        password = self.hero_pass_var.get().strip()
        vin_single = self.hero_vin_var.get().strip().upper()

        if not username or not password:
            messagebox.showwarning("Missing Credentials", "Please enter your Hero Portal User ID and Password.")
            return

        vins = []
        if self.hero_bulk_vins:
            vins = self.hero_bulk_vins
        elif vin_single:
            vins = [vin_single]
        else:
            messagebox.showwarning("Missing VIN", "Please enter a VIN number or load a vin_list.txt file.")
            return

        out_dir = self.out_entry.get().strip()
        if not out_dir:
            messagebox.showwarning("Output Missing", "Please specify a valid output directory.")
            return

        self.btn_hero_fetch.config(state="disabled")
        self.prog_var.set(5)
        self.log_text.delete(1.0, tk.END)
        self.lbl_status.config(text="Connecting to Hero Portal...")

        hypo_raw = self.hypo_var.get()
        if "Leave Blank" in hypo_raw:
            hypo_val = "BLANK"
        elif "Keep Original" in hypo_raw:
            hypo_val = "KEEP_ORIGINAL"
        else:
            hypo_val = hypo_raw.strip()

        date_val = self.date_var.get().strip()
        headless_val = self.hero_headless_var.get()
        stamp_val = self.stamp_var.get()
        scanned_val = self.scanned_var.get()
        bw_val = self.bw_var.get()

        thread = threading.Thread(
            target=self.run_hero_worker,
            args=(vins, username, password, out_dir, hypo_val, date_val, stamp_val, scanned_val, bw_val, headless_val),
            daemon=True
        )
        thread.start()

    def run_hero_worker(self, vins, username, password, out_dir, hypo_val, date_val, stamp_val, scanned_val, bw_val, headless_val):
        self.log(f"=== Hero MotoCorp Direct Auto-Download & Convert ===")
        self.log(f"User ID: {username}")
        self.log(f"VIN(s) to process: {', '.join(vins)}")
        self.log(f"Output folder: {out_dir}\n")

        latest_file = None
        total_vins = len(vins)
        success_vins = 0

        def ui_status_cb(msg):
            self.after(0, self.log, f"  {msg}")
            self.after(0, self.lbl_status.config, {"text": msg})

        try:
            results = hero_downloader.run_hero_automation_sync(
                vins=vins,
                username=username,
                password=password,
                download_dir=Path("HeroMotoCorp_Downloads"),
                output_dir=Path(out_dir),
                convert=True,
                hypothecation=hypo_val,
                new_date=date_val,
                affix_stamp=stamp_val,
                scanned_effect=scanned_val,
                bw_mode=bw_val,
                headless=headless_val,
                status_cb=ui_status_cb
            )

            for r in results:
                vin = r["vin"]
                conv_dict = r.get("converted_files", {})
                if conv_dict:
                    success_vins += 1
                    for rep_name, cinfo in conv_dict.items():
                        latest_file = cinfo["converted_path"]
                        self.log(f"✅ [1-Page <280KB] {cinfo['filename']} ({cinfo['file_size_kb']} KB)")

            self.last_converted_file = latest_file
            self.after(0, self.finish_hero_automation, success_vins, total_vins, out_dir)

        except Exception as e:
            self.after(0, self.log, f"\n❌ Automation encountered an error: {e}")
            self.after(0, self.finish_hero_automation, 0, total_vins, out_dir, str(e))

    def finish_hero_automation(self, success_vins, total_vins, out_dir, err=None):
        self.btn_hero_fetch.config(state="normal")
        self.prog_var.set(100)

        if err:
            self.lbl_status.config(text=f"Failed: {err}")
            messagebox.showerror("Download Error", f"Hero Portal error occurred:\n\n{err}")
        else:
            self.lbl_status.config(text=f"Complete! Successfully processed {success_vins}/{total_vins} VINs.")
            if self.last_converted_file:
                self.btn_open_latest.config(state="normal")
            messagebox.showinfo(
                "Hero Download & Convert Complete",
                f"Documents downloaded and converted successfully!\n\n"
                f"VINs Processed: {success_vins}/{total_vins}\n"
                f"All 3 documents (Invoice, Sale Cert, Form 22) are single-page and strictly < 280 KB.\n\n"
                f"Saved to:\n{out_dir}"
            )

    # ─── LOCAL FILE CONVERSION WORKER ─────────────────────────────────────────
    def choose_files(self):
        filenames = filedialog.askopenfilenames(
            title="Select Hero Invoices or Sale Certificates",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filenames:
            for f in filenames:
                if f not in self.input_files:
                    self.input_files.append(f)
            self.update_file_list()

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with PDFs")
        if folder:
            for root, _, files in os.walk(folder):
                for file in sorted(files):
                    if file.lower().endswith(".pdf"):
                        full_path = os.path.join(root, file)
                        if full_path not in self.input_files:
                            self.input_files.append(full_path)
            self.update_file_list()

    def clear_files(self):
        self.input_files.clear()
        self.update_file_list()

    def update_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for path in self.input_files:
            self.file_listbox.insert(tk.END, os.path.basename(path))

        count = len(self.input_files)
        if count == 0:
            self.lbl_file_count.config(text="No files selected yet")
        elif count == 1:
            self.lbl_file_count.config(text="1 document queued")
        else:
            self.lbl_file_count.config(text=f"{count} documents queued")

    def start_local_conversion(self):
        if not self.input_files:
            messagebox.showwarning("No Files Selected", "Please select at least one PDF file to convert.")
            return

        out_dir = self.out_entry.get().strip()
        if not out_dir:
            messagebox.showwarning("Output Missing", "Please specify a valid output directory.")
            return

        self.btn_convert_local.config(state="disabled")
        self.prog_var.set(0)
        self.log_text.delete(1.0, tk.END)
        self.lbl_status.config(text="Processing documents, please wait...")

        hypo_raw = self.hypo_var.get()
        if "Leave Blank" in hypo_raw:
            hypo_val = "BLANK"
        elif "Keep Original" in hypo_raw:
            hypo_val = "KEEP_ORIGINAL"
        else:
            hypo_val = hypo_raw.strip()

        date_val = self.date_var.get().strip()
        stamp_val = self.stamp_var.get()
        scanned_val = self.scanned_var.get()
        bw_val = self.bw_var.get()

        thread = threading.Thread(
            target=self.run_local_worker,
            args=(out_dir, hypo_val, date_val, stamp_val, scanned_val, bw_val),
            daemon=True
        )
        thread.start()

    def run_local_worker(self, out_dir, hypo_val, date_val, stamp_val, scanned_val, bw_val):
        os.makedirs(out_dir, exist_ok=True)
        total = len(self.input_files)

        success_count = 0
        error_count = 0
        latest_converted = None

        self.log("=== Starting local conversion to Annapurna Motors ===")
        self.log(f"Destination: {out_dir}\n")

        for idx, in_file in enumerate(self.input_files):
            fname = os.path.basename(in_file)
            stem, ext = os.path.splitext(fname)
            out_file = os.path.join(out_dir, f"{stem}_annapurna{ext}")

            try:
                res = converter.convert_document(
                    in_file,
                    out_file,
                    hypothecation=hypo_val,
                    new_date=date_val,
                    affix_stamp=stamp_val,
                    scanned_effect=scanned_val,
                    bw_mode=bw_val
                )

                success_count += 1
                latest_converted = out_file
                size_kb = res.get('file_size_kb', 0)
                doc_type = res.get('doc_type', 'doc')
                self.log(f"[OK] {fname} ({doc_type}, {size_kb} KB) -> {os.path.basename(out_file)}")
            except Exception as e:
                error_count += 1
                self.log(f"[ERROR] {fname}: {e}")

            pct = int(((idx + 1) / total) * 100)
            self.after(0, self.update_local_progress, pct, f"Processed {idx + 1} of {total} files...")

        self.last_converted_file = latest_converted
        self.after(0, self.finish_local_conversion, success_count, error_count)

    def update_local_progress(self, percent, status_msg):
        self.prog_var.set(percent)
        self.lbl_status.config(text=status_msg)

    def finish_local_conversion(self, success_count, error_count):
        self.btn_convert_local.config(state="normal")
        self.lbl_status.config(text=f"Completed! Converted: {success_count}, Errors: {error_count}")
        self.log(f"\nDone. Successfully converted: {success_count}, Errors: {error_count}")

        if self.last_converted_file:
            self.btn_open_latest.config(state="normal")

        out_path = self.out_entry.get().strip()
        messagebox.showinfo(
            "Conversion Complete",
            f"Documents converted successfully!\n\nSuccessful: {success_count}\nErrors: {error_count}\n\nSaved to: {out_path}"
        )


if __name__ == "__main__":
    app = ModernInvoiceApp()
    app.mainloop()
