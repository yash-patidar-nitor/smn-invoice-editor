"""
Hero Invoice Editor and Converter GUI Application
Provides a clean, simple, and modern interface for converting
Shanti Motors invoices to Annapurna Motors invoices.
"""

import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import converter


class ModernInvoiceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hero Invoice Converter - Shanti to Annapurna")
        self.geometry("740x760")
        self.minsize(650, 700)

        # Style configuration
        self.configure(bg="#F8FAFC")
        self.setup_styles()

        self.input_files = []
        self.output_dir = os.path.abspath("output_invoices")
        self.conversion_direction = tk.StringVar(value="shanti_to_annapurna")
        self.last_converted_file = None

        self.build_ui()

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        font_family = "Segoe UI" if sys.platform == "win32" else "Helvetica"
        self.font_title = (font_family, 16, "bold")
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
        style.configure("TRadiobutton", background="#FFFFFF", foreground="#0F172A", font=self.font_bold)

        style.configure("Primary.TButton", background="#2563EB", foreground="#FFFFFF", font=self.font_bold, borderwidth=0, padding=8)
        style.map("Primary.TButton",
                  background=[("active", "#1D4ED8"), ("disabled", "#93C5FD")],
                  foreground=[("disabled", "#FFFFFF")])

        style.configure("Secondary.TButton", background="#E2E8F0", foreground="#1E293B", font=self.font_regular, borderwidth=0, padding=6)
        style.map("Secondary.TButton", background=[("active", "#CBD5E1")])

        style.configure("Success.TButton", background="#16A34A", foreground="#FFFFFF", font=self.font_bold, borderwidth=0, padding=8)
        style.map("Success.TButton", background=[("active", "#15803D")])

        style.configure("TProgressbar", thickness=10, troughcolor="#E2E8F0", background="#2563EB")

    def build_ui(self):
        main_frame = ttk.Frame(self, padding="20 16 20 16")
        main_frame.pack(fill="both", expand=True)

        # Header Title Card
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 12))

        lbl_title = tk.Label(header_frame, text="Hero Invoice Converter", font=self.font_title, bg="#F8FAFC", fg="#0F172A")
        lbl_title.pack(anchor="w")
        lbl_desc = tk.Label(header_frame, text="Seamlessly convert dealership headers and footers for Hero MotoCorp invoices", font=self.font_sub, bg="#F8FAFC", fg="#64748B")
        lbl_desc.pack(anchor="w")

        # Card 1: Conversion Direction
        dir_card = self.create_card(main_frame, "1. Conversion Mode")
        dir_inner = ttk.Frame(dir_card, style="Card.TFrame")
        dir_inner.pack(fill="x", padx=12, pady=(4, 10))

        rb1 = ttk.Radiobutton(dir_inner, text="Shanti Motors  ➔  Annapurna Motors  (Standard)", 
                                value="shanti_to_annapurna", variable=self.conversion_direction,
                                command=self.on_direction_change)
        rb1.pack(anchor="w", pady=2)
        rb2 = ttk.Radiobutton(dir_inner, text="Annapurna Motors  ➔  Shanti Motors  (Reverse)", 
                                value="annapurna_to_shanti", variable=self.conversion_direction,
                                command=self.on_direction_change)
        rb2.pack(anchor="w", pady=2)

        # Card 2: Input Selection
        input_card = self.create_card(main_frame, "2. Select Invoices to Convert")
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

        self.lbl_file_count = ttk.Label(input_card, text="No files selected yet", style="Muted.TLabel")
        self.lbl_file_count.pack(anchor="w", padx=12, pady=(0, 10))

        # Card 3: Output Folder
        out_card = self.create_card(main_frame, "3. Output Destination")
        out_inner = ttk.Frame(out_card, style="Card.TFrame")
        out_inner.pack(fill="x", padx=12, pady=(4, 10))

        self.out_entry = ttk.Entry(out_inner, font=self.font_regular)
        self.out_entry.insert(0, self.output_dir)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_out = ttk.Button(out_inner, text="Browse...", style="Secondary.TButton", command=self.choose_output_dir)
        btn_out.pack(side="left", padx=(0, 6))

        btn_open_out = ttk.Button(out_inner, text="Open Folder", style="Secondary.TButton", command=self.open_output_dir)
        btn_open_out.pack(side="left")

        # Card 4: Action and Progress
        action_card = self.create_card(main_frame, "4. Process")
        action_inner = ttk.Frame(action_card, style="Card.TFrame")
        action_inner.pack(fill="x", padx=12, pady=(4, 8))

        self.btn_convert = ttk.Button(action_inner, text="⚡ Convert Invoices Now", style="Primary.TButton", command=self.start_conversion)
        self.btn_convert.pack(fill="x", pady=(0, 8))

        self.prog_var = tk.DoubleVar(value=0)
        self.prog_bar = ttk.Progressbar(action_inner, variable=self.prog_var, maximum=100)
        self.prog_bar.pack(fill="x", pady=(0, 4))

        self.lbl_status = ttk.Label(action_inner, text="Ready to convert.", style="Card.TLabel", font=self.font_bold)
        self.lbl_status.pack(anchor="w")

        log_frame = ttk.Frame(action_card, style="Card.TFrame")
        log_frame.pack(fill="both", expand=True, padx=12, pady=(4, 10))

        self.log_text = tk.Text(log_frame, height=5, bg="#0F172A", fg="#F8FAFC", relief="flat", font=("Consolas", 8))
        self.log_text.pack(fill="both", expand=True)

        self.btn_open_latest = ttk.Button(main_frame, text="👁 Open Converted PDF", style="Success.TButton", command=self.open_latest_pdf, state="disabled")
        self.btn_open_latest.pack(fill="x", pady=(8, 0))

    def create_card(self, parent, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=4)
        card.pack(fill="x", pady=(0, 10))

        title_lbl = ttk.Label(card, text=title, style="CardHeading.TLabel")
        title_lbl.pack(anchor="w", padx=12, pady=(8, 2))
        return card

    def on_direction_change(self):
        mode = self.conversion_direction.get()
        if mode == "shanti_to_annapurna":
            self.lbl_status.config(text="Mode: Converting Shanti Motors -> Annapurna Motors.")
        else:
            self.lbl_status.config(text="Mode: Converting Annapurna Motors -> Shanti Motors.")

    def choose_files(self):
        filenames = filedialog.askopenfilenames(
            title="Select Hero Invoice PDFs",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filenames:
            for f in filenames:
                if f not in self.input_files:
                    self.input_files.append(f)
            self.update_file_list()

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Invoice PDFs")
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
            self.lbl_file_count.config(text="1 PDF invoice queued")
        else:
            self.lbl_file_count.config(text=f"{count} PDF invoices queued")

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

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def start_conversion(self):
        if not self.input_files:
            messagebox.showwarning("No Files Selected", "Please select at least one PDF invoice to convert.")
            return

        out_dir = self.out_entry.get().strip()
        if not out_dir:
            messagebox.showwarning("Output Missing", "Please specify a valid output directory.")
            return

        self.btn_convert.config(state="disabled")
        self.prog_var.set(0)
        self.log_text.delete(1.0, tk.END)
        self.lbl_status.config(text="Processing invoices, please wait...")

        thread = threading.Thread(target=self.run_conversion_worker, args=(out_dir,), daemon=True)
        thread.start()

    def run_conversion_worker(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        total = len(self.input_files)
        direction = self.conversion_direction.get()
        prefix = "annapurna_" if direction == "shanti_to_annapurna" else "shanti_"

        success_count = 0
        error_count = 0
        latest_converted = None

        self.log(f"=== Starting conversion ({direction}) ===")
        self.log(f"Destination: {out_dir}\n")

        for idx, in_file in enumerate(self.input_files):
            fname = os.path.basename(in_file)
            out_file = os.path.join(out_dir, f"{prefix}{fname}")

            try:
                if direction == "shanti_to_annapurna":
                    res = converter.convert_shanti_to_annapurna(in_file, out_file)
                else:
                    res = converter.convert_annapurna_to_shanti(in_file, out_file)

                success_count += 1
                latest_converted = out_file
                self.log(f"[OK] {fname} (Headers: {res['headers_replaced']}, Footers: {res['footers_replaced']})")
            except Exception as e:
                error_count += 1
                self.log(f"[ERROR] {fname}: {e}")

            pct = int(((idx + 1) / total) * 100)
            self.after(0, self.update_progress, pct, f"Processed {idx + 1} of {total} files...")

        self.last_converted_file = latest_converted
        self.after(0, self.finish_conversion, success_count, error_count)

    def update_progress(self, percent, status_msg):
        self.prog_var.set(percent)
        self.lbl_status.config(text=status_msg)

    def finish_conversion(self, success_count, error_count):
        self.btn_convert.config(state="normal")
        self.lbl_status.config(text=f"Completed! Successfully converted: {success_count}, Errors: {error_count}")
        self.log(f"\nDone. Successfully converted: {success_count}, Errors: {error_count}")
        
        if self.last_converted_file:
            self.btn_open_latest.config(state="normal")

        out_path = self.out_entry.get().strip()
        messagebox.showinfo(
            "Conversion Complete",
            f"Invoice conversion completed!\n\nSuccessful: {success_count}\nErrors: {error_count}\n\nSaved to: {out_path}"
        )


if __name__ == "__main__":
    app = ModernInvoiceApp()
    app.mainloop()
