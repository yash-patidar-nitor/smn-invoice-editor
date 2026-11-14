"""
Hero MotoCorp – Siebel Portal Document Downloader & Annapurna Converter
========================================================================
Automates downloading GST Retail Invoice, Sale Certificate, and Form 22
from the Hero MotoCorp Siebel eDealer portal, and immediately converts
all 3 documents to Annapurna Motors format (strict single-page, authentic
dealer rubber stamp & signature, scanned laser B&W effect, < 280 KB).

Usage:
    python hero_downloader.py --vin MBLHAW471THEB1423
    python hero_downloader.py --username 63502S20 --password JDU#911 --vin MBLHAW471THEB1423
    python hero_downloader.py --headless --vin-file vin_list.txt
"""

import asyncio
import sys
import os
import re
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any

import aiohttp
from playwright.async_api import async_playwright, Page, BrowserContext, Locator

# Ensure converter can be imported regardless of execution working directory
script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

try:
    import converter
except ImportError:
    # If run from project root, check smn-invoice-editor subfolder
    sub_dir = script_dir / "smn-invoice-editor"
    if sub_dir.exists() and str(sub_dir) not in sys.path:
        sys.path.insert(0, str(sub_dir))
    import converter


# ─── DEFAULT CONFIGURATION ───────────────────────────────────────────────────
DEFAULT_PORTAL_URL   = "https://connect.heromotocorp.biz/siebel/app/edealerard/enu/?SWECmd=Login&SWECM=S"
DEFAULT_USERNAME     = "63502S20"
DEFAULT_PASSWORD     = "JDU#911"
DEFAULT_DOWNLOAD_DIR = Path("HeroMotoCorp_Downloads")
DEFAULT_OUTPUT_DIR   = Path("output_invoices")

REPORTS = [
    "GST Retail Invoice",
    "Sale Certificate",
    "Form22",
]

TIMEOUTS = {
    "page_load":  60_000,
    "element":    20_000,
    "search":     45_000,
    "report":     90_000,
    "download":  120_000,
}


def get_logger(download_dir: Path) -> logging.Logger:
    logger = logging.getLogger("hero_downloader")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        download_dir.mkdir(parents=True, exist_ok=True)
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s"))
        fh = logging.FileHandler(download_dir / "run_log.txt", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s"))
        logger.addHandler(sh)
        logger.addHandler(fh)
    return logger


# ─── SMART PLAYWRIGHT HELPERS ─────────────────────────────────────────────────
async def smart_click(page: Page, selectors: List[str], label: str,
                      timeout: int = 15_000, log: Optional[logging.Logger] = None) -> str:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            await loc.wait_for(state="visible", timeout=timeout)
            await loc.click()
            if log:
                log.info(f"  ✅ Clicked {label} via: {sel}")
            return sel
        except Exception:
            continue
    raise RuntimeError(f"Could not click '{label}'. None of these selectors worked: {selectors}")


async def smart_fill(page: Page, selectors: List[str], value: str,
                     label: str, timeout: int = 10_000, log: Optional[logging.Logger] = None) -> Locator:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            await loc.wait_for(state="visible", timeout=timeout)
            await loc.fill(value)
            if log:
                log.info(f"  ✅ Filled {label} via: {sel}")
            return loc
        except Exception:
            continue
    raise RuntimeError(f"Could not fill '{label}'. None of these selectors worked: {selectors}")


async def wait_for_siebel_ready(page: Page, timeout: int = 60_000, log: Optional[logging.Logger] = None) -> None:
    """Wait until Siebel loading spinner clears and view bars are visible."""
    if log:
        log.info("  ⏳ Waiting for Siebel to finish loading…")
    try:
        await page.wait_for_selector('#maskcontent', state="hidden", timeout=timeout)
    except Exception:
        pass
    await page.wait_for_selector(
        '#s_sctrl_tabScreen, [id*="tabScreen"], [name="_swescrnbar"]',
        state="visible", timeout=timeout
    )
    await page.wait_for_timeout(1_500)
    if log:
        log.info("  ✅ Siebel ready")


# ─── SIEBEL NAVIGATION & REPORT ACTIONS ─────────────────────────────────────────
async def login(page: Page, username: str, password: str, portal_url: str = DEFAULT_PORTAL_URL,
                log: Optional[logging.Logger] = None, status_cb: Optional[Callable[[str], None]] = None) -> None:
    if status_cb:
        status_cb(f"Connecting to Hero Siebel portal…")
    if log:
        log.info(f"Opening portal: {portal_url}")
    await page.goto(portal_url, wait_until="domcontentloaded", timeout=TIMEOUTS["page_load"])
    await page.wait_for_timeout(2_000)

    if status_cb:
        status_cb(f"Logging in as {username}…")
    await smart_fill(page, ['input[name="SWEUserName"]', 'input[type="text"]'], username, "username", log=log)
    await smart_fill(page, ['input[name="SWEPassword"]', 'input[type="password"]'], password, "password", log=log)
    await smart_click(page, [
        'a#s_swepi_22', 'a:has-text("Login")', 'input[type="submit"]',
        'button:has-text("Login")', 'button[type="submit"]'
    ], "login button", log=log)

    await page.wait_for_load_state("networkidle", timeout=TIMEOUTS["page_load"])
    await wait_for_siebel_ready(page, log=log)
    if log:
        log.info("Login complete ✅")
    if status_cb:
        status_cb("Logged in successfully ✅")


async def go_to_vehicle_sales(page: Page, log: Optional[logging.Logger] = None,
                              status_cb: Optional[Callable[[str], None]] = None) -> None:
    if status_cb:
        status_cb("Navigating to Vehicles section…")
    if log:
        log.info("Navigating to Vehicles tab…")
    await wait_for_siebel_ready(page, log=log)
    await smart_click(page, [
        'a:has-text("Vehicles")',
        'li:has-text("Vehicles") a',
        'td:has-text("Vehicles") a',
        '[title="Vehicles"]',
        'a:has-text("Vehicle Sales")',
        '[title="Vehicle Sales"]',
        'a[href*="vehicle"]',
    ], "Vehicles tab", timeout=TIMEOUTS["element"], log=log)

    await page.wait_for_load_state("networkidle", timeout=TIMEOUTS["search"])
    await wait_for_siebel_ready(page, log=log)
    if status_cb:
        status_cb("Vehicles view loaded ✅")


async def search_vin(page: Page, vin: str, log: Optional[logging.Logger] = None,
                     status_cb: Optional[Callable[[str], None]] = None) -> None:
    if status_cb:
        status_cb(f"Searching for VIN: {vin}…")
    if log:
        log.info(f"Searching VIN: {vin}")

    # Click Query / Magnifier button
    await smart_click(page, [
        'button[title="Vehicles List:Query"]',
        'button[title*="Query"]',
        'a[title*="Query"]',
        'button[title*="Search"]',
        'img[title*="Query"]',
    ], "Query button", timeout=TIMEOUTS["element"], log=log)

    await page.wait_for_timeout(2_500)

    # Fill VIN
    await smart_fill(page, [
        'input[name="Serial_Number"]',
        'input#1_Serial_Number',
        'input[aria-label="VIN"]',
        'input[name*="Serial"]',
        'input[placeholder="<Case Sensitive>"]:visible',
    ], vin, "VIN input", log=log)

    # Click Go / Search
    await smart_click(page, [
        'button[title="Vehicles List:Go"]',
        'button[title*=":Go"]',
        'button[title="Go"]',
        'a[title="Go"]',
        'button:has-text("Go")',
        'input[value="Go"]',
    ], "Go button", timeout=TIMEOUTS["element"], log=log)

    await page.wait_for_load_state("networkidle", timeout=TIMEOUTS["search"])
    await page.wait_for_timeout(2_000)
    if log:
        log.info(f"✅ Search complete for VIN: {vin}")
    if status_cb:
        status_cb(f"VIN {vin} found in records ✅")


async def click_invoice_link(page: Page, vin: str, log: Optional[logging.Logger] = None,
                             status_cb: Optional[Callable[[str], None]] = None) -> str:
    """Click invoice number hyperlink in results grid and return invoice number."""
    if status_cb:
        status_cb("Opening Invoice details…")
    if log:
        log.info("Looking for Invoice Number hyperlink…")

    # Check for no-records
    for no_rec_sel in ['span:has-text("No records")', 'td:has-text("0 - 0")', 'div:has-text("No records found")']:
        try:
            if await page.locator(no_rec_sel).is_visible(timeout=2_000):
                raise RuntimeError(f"VIN {vin} not found in portal database.")
        except RuntimeError:
            raise
        except Exception:
            pass

    invoice_link = None
    for sel in [
        'td[headers*="Invoice"] a',
        'td a:not(:has-text("MBLHAW"))',
        'td a',
    ]:
        try:
            locs = page.locator(sel)
            if await locs.count() > 0:
                invoice_link = locs.first
                break
        except Exception:
            continue

    if invoice_link is None:
        raise RuntimeError(f"No invoice link found for VIN {vin}")

    invoice_no = (await invoice_link.text_content() or "UNKNOWN").strip()
    if log:
        log.info(f"  Found invoice: {invoice_no}")
    await invoice_link.click()

    await page.wait_for_load_state("networkidle", timeout=TIMEOUTS["search"])
    await page.wait_for_timeout(2_000)
    if status_cb:
        status_cb(f"Invoice {invoice_no} opened ✅")
    return invoice_no


async def ensure_reports_panel_open(page: Page, log: Optional[logging.Logger] = None) -> None:
    dropdown_sel = 'select[name="s_reportNameField"]'
    if await page.locator(dropdown_sel).is_visible():
        if log:
            log.info("  ℹ️  Report panel already open")
        return

    await smart_click(page, [
        'li#tb_14',
        'li[title="Report(s)"]',
        '[aria-label="Report(s)"]',
        'li[name="Reports"]',
    ], "Reports icon", timeout=TIMEOUTS["element"], log=log)

    try:
        await page.wait_for_selector(dropdown_sel, state="visible", timeout=15_000)
    except Exception:
        await page.wait_for_timeout(1_000)
        await smart_click(page, ['li#tb_14', 'li[title="Report(s)"]'], "Reports icon (retry)", timeout=TIMEOUTS["element"], log=log)
        await page.wait_for_selector(dropdown_sel, state="visible", timeout=15_000)


async def dismiss_dialogs(page: Page) -> None:
    for sel in ['button:has-text("OK")', 'button:has-text("Close")', 'a:has-text("OK")', 'button:has-text("Cancel")']:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1_200):
                await btn.click()
                await page.wait_for_timeout(300)
        except Exception:
            pass


async def download_report(page: Page, context: BrowserContext,
                          report_name: str, vin_dir: Path, invoice_no: str,
                          log: Optional[logging.Logger] = None,
                          status_cb: Optional[Callable[[str], None]] = None) -> Optional[Path]:
    if status_cb:
        status_cb(f"Downloading report: {report_name}…")
    if log:
        log.info(f"  Requesting report: '{report_name}'")

    await ensure_reports_panel_open(page, log=log)

    dropdown = page.locator('select[name="s_reportNameField"]')
    await dropdown.wait_for(state="visible", timeout=TIMEOUTS["element"])
    await dropdown.select_option(label=report_name)
    await page.wait_for_timeout(2_000)
    await dismiss_dialogs(page)
    await page.wait_for_timeout(500)

    captured_urls: List[str] = []
    def on_request(req):
        if "SWECmd=GetFile" in req.url or "SRN=" in req.url:
            captured_urls.append(req.url)
    page.on("request", on_request)

    safe_name = re.sub(r'[\\/*?:"<>|]', "_", report_name)
    out_path = vin_dir / f"{invoice_no}_{safe_name}.pdf"

    # Attempt 1: native Playwright download event
    try:
        submit_btn = page.locator('button[title="Run Report:Submit"], button:has-text("Submit")').first
        await submit_btn.wait_for(state="visible", timeout=TIMEOUTS["element"])
        async with page.expect_download(timeout=TIMEOUTS["download"]) as dl_info:
            try:
                await submit_btn.click(timeout=5_000)
            except Exception:
                await page.evaluate("el => el.click()", await submit_btn.element_handle())
        dl = await dl_info.value
        await dl.save_as(out_path)
        page.remove_listener("request", on_request)
        if log:
            log.info(f"  ✅ Saved (native): {out_path.name}")
        await dismiss_dialogs(page)
        await page.wait_for_timeout(1_500)
        return out_path
    except Exception as e1:
        if log:
            log.warning(f"  Native download failed ({e1}), trying HTTP intercept…")

    # Attempt 2: download via intercepted URL + session cookies
    await dismiss_dialogs(page)
    if captured_urls:
        cookies = await context.cookies()
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        async with aiohttp.ClientSession() as sess:
            async with sess.get(
                captured_urls[-1],
                headers={"Cookie": cookie_str, "User-Agent": "Mozilla/5.0", "Referer": DEFAULT_PORTAL_URL},
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    out_path.write_bytes(await resp.read())
                    page.remove_listener("request", on_request)
                    if log:
                        log.info(f"  ✅ Saved (HTTP intercept): {out_path.name}")
                    return out_path
                else:
                    if log:
                        log.error(f"  ❌ HTTP {resp.status} downloading {report_name}")

    page.remove_listener("request", on_request)
    return None


# ─── HIGH-LEVEL DOWNLOAD & CONVERT PIPELINE ───────────────────────────────────
def convert_downloaded_pdf(raw_pdf_path: Path, output_dir: Path,
                           hypothecation: str = "KEEP_ORIGINAL",
                           new_date: str = "",
                           affix_stamp: bool = True,
                           scanned_effect: bool = True,
                           bw_mode: bool = True,
                           log: Optional[logging.Logger] = None) -> Optional[Dict[str, Any]]:
    """Runs converter.convert_document on a downloaded raw PDF."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        fname = raw_pdf_path.name
        stem = raw_pdf_path.stem
        # Name converted file cleanly: e.g. 63502BK26S410_GST_Retail_Invoice_annapurna.pdf
        clean_stem = re.sub(r'[\s\-]+', '_', stem)
        out_pdf_path = output_dir / f"{clean_stem}_annapurna.pdf"

        # Auto-detect target doc_type by filename pattern if possible
        doc_type = None
        lower_name = fname.lower()
        if "gst" in lower_name or "invoice" in lower_name:
            doc_type = "invoice"
        elif "sale" in lower_name or "cert" in lower_name:
            doc_type = "sale_certificate"
        elif "form" in lower_name or "22" in lower_name:
            doc_type = "form_22"

        stats = converter.convert_document(
            str(raw_pdf_path),
            str(out_pdf_path),
            doc_type=doc_type,
            hypothecation=hypothecation,
            new_date=new_date,
            affix_stamp=affix_stamp,
            scanned_effect=scanned_effect,
            bw_mode=bw_mode
        )

        size_kb = round(out_pdf_path.stat().st_size / 1024.0, 1)
        res = {
            "raw_path": str(raw_pdf_path),
            "converted_path": str(out_pdf_path),
            "filename": out_pdf_path.name,
            "doc_type": stats.get("doc_type", doc_type or "invoice"),
            "file_size_kb": size_kb,
            "status": "success"
        }
        if log:
            log.info(f"  ✨ Converted {out_pdf_path.name} ({size_kb} KB, 1 Page)")
        return res
    except Exception as e:
        if log:
            log.error(f"  ❌ Conversion failed for {raw_pdf_path.name}: {e}")
        return None


async def download_and_convert_vin(
    page: Page,
    context: BrowserContext,
    vin: str,
    download_dir: Path = DEFAULT_DOWNLOAD_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    convert: bool = True,
    hypothecation: str = "KEEP_ORIGINAL",
    new_date: str = "",
    affix_stamp: bool = True,
    scanned_effect: bool = True,
    bw_mode: bool = True,
    log: Optional[logging.Logger] = None,
    status_cb: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """
    Downloads all 3 reports for a single VIN, then converts them to Annapurna Motors format.
    Saves converted files into output_dir (or output_dir / vin).
    """
    result: Dict[str, Any] = {
        "vin": vin,
        "invoice_no": "",
        "raw_files": {},
        "converted_files": {},
        "error": ""
    }

    try:
        await go_to_vehicle_sales(page, log=log, status_cb=status_cb)
        await search_vin(page, vin, log=log, status_cb=status_cb)
        invoice_no = await click_invoice_link(page, vin, log=log, status_cb=status_cb)
        result["invoice_no"] = invoice_no

        raw_vin_dir = download_dir / vin
        raw_vin_dir.mkdir(parents=True, exist_ok=True)

        target_out_dir = output_dir / vin
        target_out_dir.mkdir(parents=True, exist_ok=True)

        for report in REPORTS:
            dl_path = await download_report(
                page, context, report, raw_vin_dir, invoice_no,
                log=log, status_cb=status_cb
            )
            if dl_path and dl_path.exists():
                result["raw_files"][report] = str(dl_path)
                if convert:
                    if status_cb:
                        status_cb(f"Converting {report} to Annapurna format…")
                    conv_info = convert_downloaded_pdf(
                        dl_path, target_out_dir,
                        hypothecation=hypothecation,
                        new_date=new_date,
                        affix_stamp=affix_stamp,
                        scanned_effect=scanned_effect,
                        bw_mode=bw_mode,
                        log=log
                    )
                    if conv_info:
                        result["converted_files"][report] = conv_info
            else:
                result["raw_files"][report] = None
            await page.wait_for_timeout(1_000)

        if status_cb:
            conv_count = len(result["converted_files"]) if convert else 0
            raw_count = sum(1 for v in result["raw_files"].values() if v)
            status_cb(f"VIN {vin} finished: {raw_count}/3 downloaded, {conv_count}/3 converted ✅")

    except Exception as e:
        err_msg = str(e)
        result["error"] = err_msg
        if log:
            log.error(f"  ❌ Error processing VIN {vin}: {err_msg}")
        if status_cb:
            status_cb(f"❌ Error on VIN {vin}: {err_msg}")
        try:
            await go_to_vehicle_sales(page, log=log)
        except Exception:
            pass

    return result


async def run_hero_automation(
    vins: List[str],
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
    portal_url: str = DEFAULT_PORTAL_URL,
    download_dir: Path = DEFAULT_DOWNLOAD_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    convert: bool = True,
    hypothecation: str = "KEEP_ORIGINAL",
    new_date: str = "",
    affix_stamp: bool = True,
    scanned_effect: bool = True,
    bw_mode: bool = True,
    headless: bool = True,
    status_cb: Optional[Callable[[str], None]] = None
) -> List[Dict[str, Any]]:
    """
    Main orchestration function: launches Playwright, logs into Siebel,
    iterates through VINs, downloads and converts the 3 reports for each.
    """
    log = get_logger(download_dir)
    results = []

    async with async_playwright() as p:
        if status_cb:
            status_cb("Starting browser session on web server…")
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--start-maximized"
            ]
        )
        context = await browser.new_context(
            accept_downloads=True,
            viewport={"width": 1366, "height": 768}
        )
        page = await context.new_page()

        try:
            await login(page, username, password, portal_url=portal_url, log=log, status_cb=status_cb)
            total = len(vins)
            for idx, vin in enumerate(vins, 1):
                clean_vin = vin.strip().upper()
                if not clean_vin or clean_vin.startswith("#"):
                    continue
                if status_cb:
                    status_cb(f"[{idx}/{total}] Processing VIN: {clean_vin}")
                res = await download_and_convert_vin(
                    page, context, clean_vin,
                    download_dir=download_dir,
                    output_dir=output_dir,
                    convert=convert,
                    hypothecation=hypothecation,
                    new_date=new_date,
                    affix_stamp=affix_stamp,
                    scanned_effect=scanned_effect,
                    bw_mode=bw_mode,
                    log=log,
                    status_cb=status_cb
                )
                results.append(res)
                if idx < total:
                    await page.wait_for_timeout(2_000)

            if status_cb:
                status_cb("All VINs processed successfully! 🎉")
        finally:
            await browser.close()

    return results


# ─── SYNCHRONOUS RUNNER FOR THREADED WORKERS ──────────────────────────────────
def run_hero_automation_sync(
    vins: List[str],
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
    portal_url: str = DEFAULT_PORTAL_URL,
    download_dir: Path = DEFAULT_DOWNLOAD_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    convert: bool = True,
    hypothecation: str = "KEEP_ORIGINAL",
    new_date: str = "",
    affix_stamp: bool = True,
    scanned_effect: bool = True,
    bw_mode: bool = True,
    headless: bool = True,
    status_cb: Optional[Callable[[str], None]] = None
) -> List[Dict[str, Any]]:
    return asyncio.run(
        run_hero_automation(
            vins=vins,
            username=username,
            password=password,
            portal_url=portal_url,
            download_dir=download_dir,
            output_dir=output_dir,
            convert=convert,
            hypothecation=hypothecation,
            new_date=new_date,
            affix_stamp=affix_stamp,
            scanned_effect=scanned_effect,
            bw_mode=bw_mode,
            headless=headless,
            status_cb=status_cb
        )
    )


# ─── CLI ENTRYPOINT ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hero MotoCorp Siebel Downloader & Annapurna Converter")
    parser.add_argument("--vin", type=str, default=None, help="Single VIN number")
    parser.add_argument("--vin-file", type=str, default="vin_list.txt", help="Path to text file with VINs")
    parser.add_argument("--username", "-u", type=str, default=DEFAULT_USERNAME, help="Portal username")
    parser.add_argument("--password", "-p", type=str, default=DEFAULT_PASSWORD, help="Portal password")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--output-dir", "-o", type=str, default="output_invoices", help="Folder for converted documents")
    parser.add_argument("--download-dir", "-d", type=str, default="HeroMotoCorp_Downloads", help="Folder for raw downloads")
    parser.add_argument("--no-convert", action="store_true", help="Download raw files only without converting")
    parser.add_argument("--hypothecation", type=str, default="KEEP_ORIGINAL")
    parser.add_argument("--date", type=str, default="")
    parser.add_argument("--no-stamp", action="store_true", help="Do not affix dealer rubber stamp")
    parser.add_argument("--no-scanned", action="store_true", help="Keep clean digital vector look")
    parser.add_argument("--color", action="store_true", help="Preserve color scan instead of laser B&W")

    args = parser.parse_args()

    vins_to_run = []
    if args.vin:
        vins_to_run = [args.vin.strip().upper()]
    elif os.path.exists(args.vin_file):
        with open(args.vin_file, "r", encoding="utf-8") as f:
            vins_to_run = [line.strip().upper() for line in f if line.strip() and not line.startswith("#")]
    else:
        print(f"Error: Specify --vin or provide {args.vin_file}")
        sys.exit(1)

    print(f"Starting Hero Downloader for {len(vins_to_run)} VIN(s)...")
    res_list = run_hero_automation_sync(
        vins=vins_to_run,
        username=args.username,
        password=args.password,
        download_dir=Path(args.download_dir),
        output_dir=Path(args.output_dir),
        convert=not args.no_convert,
        hypothecation=args.hypothecation,
        new_date=args.date,
        affix_stamp=not args.no_stamp,
        scanned_effect=not args.no_scanned,
        bw_mode=not args.color,
        headless=args.headless,
        status_cb=lambda msg: print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    )

    print("\n" + "="*60)
    print("DOWNLOAD & CONVERSION SUMMARY")
    print("="*60)
    for r in res_list:
        v = r["vin"]
        inv = r["invoice_no"]
        conv_items = list(r["converted_files"].keys())
        print(f"VIN: {v} | Invoice: {inv} | Converted: {', '.join(conv_items) if conv_items else 'None'}")
        for cname, cinfo in r["converted_files"].items():
            print(f"   -> {cname}: {cinfo['converted_path']} ({cinfo['file_size_kb']} KB)")
    print("="*60)
