"""
Hero Invoice & Sale Certificate Converter - Web Application Server
Flask-based responsive web app with drag-and-drop conversion,
live PDF preview, simultaneous batch processing of Invoices and Sale Certificates,
Direct Hero Portal Auto-Download & Convert (Playwright automation),
User ID / Password configuration, Hypothecation dropdown, Date picker, and ZIP download.
"""

import os
import io
import re
import zipfile
import tempfile
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template_string
from werkzeug.utils import secure_filename
import fitz
import converter
import hero_downloader

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB max upload

CONVERTED_STORE = {}

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hero Invoice & Sale Certificate Converter - Annapurna Motors</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --text-dark: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --success: #16a34a;
            --success-bg: #f0fdf4;
            --radius: 12px;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg-color); color: var(--text-dark); padding: 28px 16px; min-height: 100vh; }
        .container { max-width: 860px; margin: 0 auto; }
        
        .header { margin-bottom: 24px; text-align: center; }
        .badge { display: inline-block; padding: 4px 14px; background: #dbeafe; color: var(--primary); font-size: 12px; font-weight: 600; border-radius: 9999px; margin-bottom: 8px; }
        .title { font-size: 28px; font-weight: 700; color: var(--text-dark); letter-spacing: -0.5px; }
        .subtitle { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
        
        .card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 22px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
        .card-title { font-size: 15px; font-weight: 600; margin-bottom: 14px; color: var(--text-dark); display: flex; align-items: center; gap: 8px; }

        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 6px; }
        @media (max-width: 640px) { .form-grid { grid-template-columns: 1fr; } }

        .form-group { display: flex; flex-direction: column; gap: 6px; }
        .form-label { font-size: 13px; font-weight: 600; color: var(--text-dark); }
        .form-hint { font-size: 11px; color: var(--text-muted); }
        .form-control { width: 100%; border: 1px solid var(--border-color); border-radius: 8px; padding: 10px 12px; font-size: 13px; color: var(--text-dark); background: #fff; transition: border-color 0.2s; outline: none; }
        .form-control:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(37,99,235,0.1); }

        /* Mode Tabs */
        .tabs { display: flex; gap: 6px; margin-bottom: 20px; background: #e2e8f0; padding: 4px; border-radius: 10px; flex-wrap: wrap; }
        .tab-btn { flex: 1; min-width: 140px; padding: 10px 12px; border: none; border-radius: 8px; font-size: 13.5px; font-weight: 600; cursor: pointer; color: var(--text-muted); background: transparent; transition: all 0.2s; text-align: center; }
        .tab-btn.active { background: #fff; color: var(--primary); box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
        .tab-btn.hero-tab { color: #1d4ed8; font-weight: 700; }
        .tab-btn.hero-tab.active { background: #2563eb; color: #fff; }

        .drop-zone { display: block; border: 2px dashed #cbd5e1; border-radius: var(--radius); padding: 32px 20px; text-align: center; cursor: pointer; transition: all 0.2s; background: #f8fafc; }
        .drop-zone:hover, .drop-zone.dragover { border-color: var(--primary); background: #eff6ff; }
        .drop-zone-icon { font-size: 38px; margin-bottom: 8px; }
        .drop-zone-title { font-size: 15px; font-weight: 600; color: var(--text-dark); }
        .drop-zone-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
        .btn-browse { display: inline-block; margin-top: 12px; background: #eff6ff; color: var(--primary); border: 1px solid #bfdbfe; border-radius: 6px; padding: 8px 18px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-browse:hover { background: #dbeafe; }
        
        .file-list { margin-top: 16px; display: none; }
        .selection-banner { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #1e40af; font-weight: 500; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; }
        .file-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: #f1f5f9; border-radius: 8px; margin-bottom: 6px; font-size: 13px; }
        .file-name { font-weight: 500; color: var(--text-dark); }
        .file-size { color: var(--text-muted); font-size: 12px; margin-left: 6px; }
        .file-remove { color: #ef4444; cursor: pointer; font-weight: 600; padding: 2px 8px; border-radius: 4px; }
        .file-remove:hover { background: #fee2e2; }

        .btn-convert { width: 100%; background: var(--primary); color: #fff; border: none; padding: 14px; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.2s; margin-top: 14px; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .btn-convert:hover { background: var(--primary-hover); }
        .btn-convert:disabled { background: #93c5fd; cursor: not-allowed; }

        .progress-box { margin-top: 16px; display: none; }
        .progress-bar-container { background: #e2e8f0; border-radius: 9999px; height: 8px; overflow: hidden; margin-bottom: 8px; }
        .progress-bar-fill { background: var(--primary); height: 100%; width: 0%; transition: width 0.3s; }
        .progress-status { font-size: 13px; font-weight: 500; color: var(--text-muted); }

        .results-box { margin-top: 20px; display: none; }
        .success-banner { background: var(--success-bg); border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
        .success-text { color: #15803d; font-size: 14px; font-weight: 600; }
        .btn-download-all { background: var(--success); color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
        .btn-download-all:hover { background: #15803d; }

        .result-item { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 8px; font-size: 13px; background: #fff; }
        .result-type-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-right: 6px; }
        .tag-inv { background: #e0e7ff; color: #4338ca; }
        .tag-sc { background: #fef3c7; color: #b45309; }
        .tag-f22 { background: #dcfce7; color: #15803d; }
        .result-actions { display: flex; gap: 8px; }
        .btn-link { font-size: 12px; font-weight: 600; text-decoration: none; padding: 6px 12px; border-radius: 4px; border: none; cursor: pointer; }
        .btn-preview { background: #eff6ff; color: var(--primary); }
        .btn-download { background: #f1f5f9; color: var(--text-dark); }
        
        .preview-modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.7); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
        .preview-content { background: #fff; width: 100%; max-width: 900px; height: 90vh; border-radius: var(--radius); display: flex; flex-direction: column; overflow: hidden; }
        .preview-header { padding: 14px 20px; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; }
        .preview-title { font-size: 15px; font-weight: 600; }
        .preview-close { background: none; border: none; font-size: 20px; cursor: pointer; color: var(--text-muted); }
        .preview-iframe { flex: 1; border: none; width: 100%; height: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">Shanti Motors ➔ Annapurna Motors • Auto-Downloader Enabled</span>
            <h1 class="title">Hero Document Converter</h1>
            <p class="subtitle">Direct Hero Portal 3-Document Auto-Download & Strict 1-Page Annapurna Converter</p>
        </div>

        <!-- Mode Selector Tabs -->
        <div class="tabs">
            <button class="tab-btn hero-tab active" id="tab-hero" onclick="switchMode('hero')">⚡ Hero Portal Direct</button>
            <button class="tab-btn" id="tab-batch" onclick="switchMode('batch')">📁 Batch Upload (Local)</button>
            <button class="tab-btn" id="tab-invoice" onclick="switchMode('invoice')">🧾 Tax Invoice</button>
            <button class="tab-btn" id="tab-sc" onclick="switchMode('sale-cert')">📜 Sale Certificate</button>
            <button class="tab-btn" id="tab-f22" onclick="switchMode('form-22')">📋 Form 22</button>
        </div>

        <!-- Options Card -->
        <div class="card">
            <div class="card-title">1. Document Options (Optional)</div>
            <div class="form-grid">
                <div class="form-group">
                    <label class="form-label">Hypothecation With</label>
                    <select class="form-control" id="hypo-select">
                        <option value="KEEP_ORIGINAL">Keep Original (No Change)</option>
                        <option value="HERO FINCORP LTD">HERO FINCORP LTD</option>
                        <option value="TATA CAPITAL LTD">TATA CAPITAL LTD</option>
                        <option value="AASTHA SAKH SAHKARITA">AASTHA SAKH SAHKARITA</option>
                        <option value="BLANK">Leave Blank (Cash / None)</option>
                    </select>
                    <span class="form-hint">Updates the hypothecation financier</span>
                </div>
                <div class="form-group">
                    <label class="form-label">Change Date</label>
                    <input type="text" class="form-control" id="date-input" placeholder="e.g. 15/11/2026 (Leave blank for original)">
                    <span class="form-hint">Format: DD/MM/YYYY. Preserves original invoice time.</span>
                </div>
            </div>
            <div style="margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border-color);">
                <label style="display: flex; align-items: center; gap: 10px; background: #eff6ff; border: 1px solid #bfdbfe; padding: 12px 16px; border-radius: 8px; cursor: pointer; user-select: none;">
                    <input type="checkbox" id="stamp-checkbox" checked style="width: 18px; height: 18px; accent-color: var(--primary); cursor: pointer;">
                    <span style="font-size: 13.5px; font-weight: 600; color: #1e40af;">
                        ✍️ Affix Annapurna Motors Stamp & Signature (Ready for RTO Upload)
                    </span>
                </label>
                <span class="form-hint" style="margin-top: 6px; display: block; margin-left: 4px;">
                    Automates Step 3: Overlays authentic Annapurna Motors circular rubber stamp and signature onto the signatory block.
                </span>
            </div>
            <div style="margin-top: 10px;">
                <label style="display: flex; align-items: center; gap: 10px; background: #fefce8; border: 1px solid #fef08a; padding: 12px 16px; border-radius: 8px; cursor: pointer; user-select: none;">
                    <input type="checkbox" id="scanned-look-checkbox" checked style="width: 18px; height: 18px; accent-color: #ca8a04; cursor: pointer;">
                    <span style="font-size: 13.5px; font-weight: 600; color: #854d0e;">
                        📄 Realistic Scanned Look (Scan & Print Imperfections, Dull Colors, Anti-Digital Look)
                    </span>
                </label>
                <span class="form-hint" style="margin-top: 6px; display: block; margin-left: 4px;">
                    Simulates physical print & ADF feeder scan: adds authentic tilt, toner specks, and paper grain. Strictly under 280 KB.
                </span>
            </div>
            <div style="margin-top: 10px;">
                <label style="display: flex; align-items: center; gap: 10px; background: #f8fafc; border: 1px solid #cbd5e1; padding: 12px 16px; border-radius: 8px; cursor: pointer; user-select: none;">
                    <input type="checkbox" id="bw-mode-checkbox" checked style="width: 18px; height: 18px; accent-color: #334155; cursor: pointer;">
                    <span style="font-size: 13.5px; font-weight: 600; color: #1e293b;">
                        🖨️ Black & White Scanner & Printer Mode (Monochrome laser text + color rubber seal)
                    </span>
                </label>
            </div>
        </div>

        <!-- HERO PORTAL AUTOMATION CARD (Active by default) -->
        <div class="card" id="hero-card">
            <div class="card-title">2. Hero Portal Auto-Download & Convert</div>
            
            <div class="form-grid" style="margin-bottom: 12px;">
                <div class="form-group">
                    <label class="form-label">Hero Portal User ID</label>
                    <input type="text" class="form-control" id="hero-user" value="63502S20" placeholder="e.g. 63502S20">
                    <span class="form-hint">Dealer account username</span>
                </div>
                <div class="form-group">
                    <label class="form-label">Hero Portal Password</label>
                    <div style="display: flex; gap: 8px;">
                        <input type="password" class="form-control" id="hero-pass" value="JDU#911" placeholder="Enter password">
                        <button type="button" class="btn-link" style="background:#e2e8f0; color:#334155;" onclick="togglePasswordVisibility()">👁</button>
                    </div>
                    <span class="form-hint">Dealer portal credentials</span>
                </div>
            </div>

            <div class="form-group" style="margin-bottom: 12px;">
                <label class="form-label">VIN Number(s)</label>
                <input type="text" class="form-control" id="hero-vin" value="MBLHAW471THEB1423" placeholder="e.g. MBLHAW471THEB1423 (or multiple separated by commas)">
                <span class="form-hint">Downloads: 1. GST Retail Invoice, 2. Form 21 Sale Certificate, 3. Form 22.</span>
            </div>

            <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 10px; margin-bottom: 14px;">
                <label style="font-size: 13px; color: var(--text-muted); display: flex; align-items: center; gap: 6px; cursor: pointer;">
                    <input type="checkbox" id="hero-headless" checked style="accent-color: var(--primary);">
                    Run browser silently in background (Headless)
                </label>
            </div>

            <button class="btn-convert" id="btn-hero-start" onclick="startHeroDownload()">
                🚀 Fetch 3 Documents from Hero Portal & Convert to Annapurna Motors
            </button>

            <div class="progress-box" id="hero-progress-box">
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" id="hero-progress-fill"></div>
                </div>
                <div class="progress-status" id="hero-progress-status">Initiating Hero portal connection...</div>
            </div>
        </div>

        <!-- LOCAL UPLOAD CARD (Used when switching to local tabs) -->
        <div class="card" id="local-upload-card" style="display: none;">
            <div class="card-title" id="upload-card-title">2. Upload Documents</div>
            
            <input type="file" id="file-input" multiple accept=".pdf,.PDF,application/pdf" style="position:fixed; top:-2000px; left:-2000px; opacity:0; pointer-events:none;">

            <label for="file-input" class="drop-zone" id="drop-zone">
                <div class="drop-zone-icon" id="drop-zone-icon">⚡</div>
                <div class="drop-zone-title" id="drop-zone-title">Click anywhere to select or drag & drop files</div>
                <div class="drop-zone-desc" id="drop-zone-desc">Original template is 100% preserved with zero font truncation.</div>
                <span class="btn-browse" id="btn-browse-text">📁 Browse & Select Files</span>
            </label>

            <div class="file-list" id="file-list"></div>

            <button class="btn-convert" id="btn-convert" onclick="startLocalConversion()" disabled>
                ⚡ Convert All Documents to Annapurna Motors
            </button>

            <div class="progress-box" id="local-progress-box">
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" id="local-progress-fill"></div>
                </div>
                <div class="progress-status" id="local-progress-status">Processing...</div>
            </div>
        </div>

        <!-- RESULTS CARD -->
        <div class="card results-box" id="results-box">
            <div class="card-title">3. Converted Annapurna Documents</div>
            <div class="success-banner">
                <div class="success-text" id="success-summary">All documents converted successfully!</div>
                <a href="#" class="btn-download-all" id="btn-download-all">📦 Download All as ZIP</a>
            </div>
            <div id="results-list"></div>
        </div>
    </div>

    <!-- Preview Modal -->
    <div class="preview-modal" id="preview-modal">
        <div class="preview-content">
            <div class="preview-header">
                <div class="preview-title" id="preview-filename">Converted Document Preview</div>
                <button class="preview-close" onclick="closePreview()">&times;</button>
            </div>
            <iframe class="preview-iframe" id="preview-iframe"></iframe>
        </div>
    </div>

    <script>
        let currentMode = 'hero';
        let selectedFiles = [];

        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');

        function togglePasswordVisibility() {
            const p = document.getElementById('hero-pass');
            p.type = p.type === 'password' ? 'text' : 'password';
        }

        function switchMode(mode) {
            currentMode = mode;
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            
            const tabEl = document.getElementById(
                mode === 'hero' ? 'tab-hero' :
                mode === 'invoice' ? 'tab-invoice' :
                mode === 'sale-cert' ? 'tab-sc' :
                mode === 'form-22' ? 'tab-f22' : 'tab-batch'
            );
            if (tabEl) tabEl.classList.add('active');

            const heroCard = document.getElementById('hero-card');
            const localCard = document.getElementById('local-upload-card');

            if (mode === 'hero') {
                heroCard.style.display = 'block';
                localCard.style.display = 'none';
            } else {
                heroCard.style.display = 'none';
                localCard.style.display = 'block';

                const uploadTitle = document.getElementById('upload-card-title');
                const dropIcon = document.getElementById('drop-zone-icon');
                const dropTitle = document.getElementById('drop-zone-title');
                const dropDesc = document.getElementById('drop-zone-desc');
                const browseText = document.getElementById('btn-browse-text');

                if (mode === 'invoice') {
                    uploadTitle.innerText = '2. Upload Tax Invoice(s)';
                    dropIcon.innerText = '🧾';
                    dropTitle.innerText = 'Click anywhere to select or drag & drop Tax Invoices';
                    dropDesc.innerText = 'Original template is 100% preserved with zero font truncation.';
                    browseText.innerText = '📁 Browse & Select Invoices';
                } else if (mode === 'sale-cert') {
                    uploadTitle.innerText = '2. Upload Sale Certificate(s) - Form 21';
                    dropIcon.innerText = '📜';
                    dropTitle.innerText = 'Click anywhere to select or drag & drop Sale Certificates';
                    dropDesc.innerText = 'Updates top date, delivery clause date, header, and signatory cleanly.';
                    browseText.innerText = '📁 Browse & Select Sale Certificates';
                } else if (mode === 'form-22') {
                    uploadTitle.innerText = '2. Upload Form 22 Certificate(s)';
                    dropIcon.innerText = '📋';
                    dropTitle.innerText = 'Click anywhere to select or drag & drop Form 22';
                    dropDesc.innerText = 'Affixes dealer stamp & signature in bottom-left blank space.';
                    browseText.innerText = '📁 Browse & Select Form 22';
                } else {
                    uploadTitle.innerText = '2. Upload Documents (Batch)';
                    dropIcon.innerText = '⚡';
                    dropTitle.innerText = 'Click anywhere to select or drag & drop files';
                    dropDesc.innerText = 'Simultaneously convert Invoices, Form 21 Sale Certificates & Form 22 in one batch!';
                    browseText.innerText = '📁 Browse & Select Files';
                }
                clearAllFiles();
            }
        }

        // File selection handler
        if (fileInput) {
            fileInput.addEventListener('change', function() {
                if (this.files && this.files.length > 0) {
                    addFiles(Array.from(this.files));
                    this.value = '';
                }
            });
        }

        window.addEventListener('dragover', (e) => e.preventDefault());
        window.addEventListener('drop', (e) => e.preventDefault());

        if (dropZone) {
            dropZone.addEventListener('dragenter', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
            dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
            dropZone.addEventListener('dragleave', (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); });
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                if (e.dataTransfer && e.dataTransfer.files) {
                    addFiles(Array.from(e.dataTransfer.files));
                }
            });
        }

        function addFiles(files) {
            files.forEach(f => {
                const lower = f.name.toLowerCase();
                if (lower.endsWith('.pdf')) {
                    if (!selectedFiles.some(existing => existing.name === f.name)) {
                        selectedFiles.push(f);
                    }
                }
            });
            renderFileList();
        }

        function removeFile(index) {
            selectedFiles.splice(index, 1);
            renderFileList();
        }

        function clearAllFiles() {
            selectedFiles = [];
            renderFileList();
        }

        function getFileBadge(name) {
            const lower = name.toLowerCase();
            if (lower.includes('22') || lower.includes('road')) {
                return '<span class="result-type-tag tag-f22">Form 22</span>';
            }
            if (lower.includes('sale') || lower.includes('cert') || lower.includes('21')) {
                return '<span class="result-type-tag tag-sc">Sale Cert</span>';
            }
            return '<span class="result-type-tag tag-inv">Tax Invoice</span>';
        }

        function renderFileList() {
            const list = document.getElementById('file-list');
            const btn = document.getElementById('btn-convert');
            if (selectedFiles.length === 0) {
                list.style.display = 'none';
                list.innerHTML = '';
                btn.disabled = true;
                return;
            }

            let html = `<div class="selection-banner">
                <span>📁 Selected <strong>${selectedFiles.length}</strong> PDF document(s)</span>
                <span style="cursor:pointer; color:#ef4444; font-weight:600;" onclick="clearAllFiles()">Clear All</span>
            </div>`;

            selectedFiles.forEach((f, idx) => {
                const sizeKb = (f.size / 1024).toFixed(1);
                html += `
                <div class="file-item">
                    <div>
                        ${getFileBadge(f.name)}
                        <span class="file-name">${f.name}</span>
                        <span class="file-size">(${sizeKb} KB)</span>
                    </div>
                    <span class="file-remove" onclick="removeFile(${idx})">&times;</span>
                </div>`;
            });

            list.innerHTML = html;
            list.style.display = 'block';
            btn.disabled = false;
        }

        // ─── HERO PORTAL AUTOMATION HANDLER ──────────────────────────────────
        async function startHeroDownload() {
            const userId = document.getElementById('hero-user').value.trim();
            const password = document.getElementById('hero-pass').value.trim();
            const vin = document.getElementById('hero-vin').value.trim();

            if (!userId || !password) {
                alert('Please enter your Hero Portal User ID and Password.');
                return;
            }
            if (!vin) {
                alert('Please enter at least one VIN number.');
                return;
            }

            const hypo = document.getElementById('hypo-select').value;
            const dateVal = document.getElementById('date-input').value.trim();
            const affixStamp = document.getElementById('stamp-checkbox').checked;
            const scannedLook = document.getElementById('scanned-look-checkbox').checked;
            const bwMode = document.getElementById('bw-mode-checkbox').checked;
            const headless = document.getElementById('hero-headless').checked;

            const btn = document.getElementById('btn-hero-start');
            btn.disabled = true;
            btn.innerText = '⏳ Connecting & Fetching from Hero Portal...';

            const pBox = document.getElementById('hero-progress-box');
            const pFill = document.getElementById('hero-progress-fill');
            const pStatus = document.getElementById('hero-progress-status');
            pBox.style.display = 'block';
            pFill.style.width = '20%';
            pStatus.innerText = 'Connecting to Hero Portal & logging in…';

            const resultsBox = document.getElementById('results-box');
            resultsBox.style.display = 'none';

            let timer = setInterval(() => {
                let cur = parseInt(pFill.style.width) || 20;
                if (cur < 85) {
                    pFill.style.width = (cur + 5) + '%';
                    if (cur === 35) pStatus.innerText = 'Navigating to Vehicles & searching VIN ' + vin + '…';
                    if (cur === 55) pStatus.innerText = 'Opening Invoice & requesting 3 reports (Invoice, Sale Cert, Form 22)…';
                    if (cur === 75) pStatus.innerText = 'Converting documents to Annapurna Motors (Single-Page, <280 KB)…';
                }
            }, 3000);

            try {
                const resp = await fetch('/api/hero-download-and-convert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        password: password,
                        vin: vin,
                        hypothecation: hypo,
                        new_date: dateVal,
                        affix_stamp: affixStamp,
                        scanned_look: scannedLook,
                        bw_mode: bwMode,
                        headless: headless
                    })
                });

                clearInterval(timer);
                pFill.style.width = '100%';

                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({ error: 'Request failed' }));
                    throw new Error(err.error || 'Server error occurred during download');
                }

                const data = await resp.json();
                pStatus.innerText = 'All documents downloaded and converted successfully! ✅';
                renderResults(data);

            } catch (err) {
                clearInterval(timer);
                pFill.style.width = '0%';
                pBox.style.display = 'none';
                alert('Hero Portal Automation Error:\n' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerText = '🚀 Fetch 3 Documents from Hero Portal & Convert to Annapurna Motors';
            }
        }

        // ─── LOCAL CONVERSION HANDLER ─────────────────────────────────────────
        async function startLocalConversion() {
            if (selectedFiles.length === 0) return;

            const btn = document.getElementById('btn-convert');
            btn.disabled = true;
            btn.innerText = '⏳ Converting Documents...';

            const pBox = document.getElementById('local-progress-box');
            const pFill = document.getElementById('local-progress-fill');
            const pStatus = document.getElementById('local-progress-status');
            pBox.style.display = 'block';
            pFill.style.width = '40%';
            pStatus.innerText = `Processing ${selectedFiles.length} file(s)...`;

            const resultsBox = document.getElementById('results-box');
            resultsBox.style.display = 'none';

            const formData = new FormData();
            selectedFiles.forEach(f => formData.append('files', f));

            formData.append('hypothecation', document.getElementById('hypo-select').value);
            formData.append('new_date', document.getElementById('date-input').value.trim());
            formData.append('affix_stamp', document.getElementById('stamp-checkbox').checked);
            formData.append('scanned_look', document.getElementById('scanned-look-checkbox').checked);
            formData.append('bw_mode', document.getElementById('bw-mode-checkbox').checked);
            formData.append('doc_mode', currentMode);

            try {
                const resp = await fetch('/api/convert', { method: 'POST', body: formData });
                if (!resp.ok) {
                    const err = await resp.json();
                    throw new Error(err.error || 'Conversion failed');
                }
                const data = await resp.json();
                pFill.style.width = '100%';
                pStatus.innerText = 'Conversion Complete!';
                renderResults(data);
            } catch (err) {
                alert('Conversion Error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerText = '⚡ Convert All Documents to Annapurna Motors';
                pBox.style.display = 'none';
            }
        }

        function renderResults(data) {
            const resultsBox = document.getElementById('results-box');
            const resultsList = document.getElementById('results-list');
            const summary = document.getElementById('success-summary');
            const zipBtn = document.getElementById('btn-download-all');

            summary.innerText = `Successfully converted ${data.files.length} document(s) to Annapurna Motors (Strict Single-Page < 280 KB)!`;
            zipBtn.href = `/api/download-zip?token=${data.token}`;

            let html = '';
            data.files.forEach(f => {
                const badge = getFileBadge(f.converted_name || f.report_name || '');
                html += `
                <div class="result-item">
                    <div>
                        ${badge}
                        <strong>${f.converted_name}</strong>
                        <span class="file-size">(${f.file_size_kb} KB • 1 Page • Scanned B&W)</span>
                    </div>
                    <div class="result-actions">
                        <button class="btn-link btn-preview" onclick="openPreview('${f.id}', '${f.converted_name}')">👁 Preview</button>
                        <a href="/api/download/${f.id}" class="btn-link btn-download">💾 Download</a>
                    </div>
                </div>`;
            });

            resultsList.innerHTML = html;
            resultsBox.style.display = 'block';
            resultsBox.scrollIntoView({ behavior: 'smooth' });
        }

        function openPreview(id, name) {
            document.getElementById('preview-filename').innerText = 'Preview: ' + name;
            document.getElementById('preview-iframe').src = `/api/preview/${id}`;
            document.getElementById('preview-modal').style.display = 'flex';
        }

        function closePreview() {
            document.getElementById('preview-modal').style.display = 'none';
            document.getElementById('preview-iframe').src = '';
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    html_path = os.path.join(os.path.dirname(__file__), 'index.html')
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/hero-download-and-convert', methods=['POST', 'OPTIONS'])
def api_hero_download_and_convert():
    if request.method == 'OPTIONS':
        return ('', 204)

    data = request.get_json(silent=True) or request.form
    user_id = (data.get('user_id') or '').strip() or hero_downloader.DEFAULT_USERNAME
    password = (data.get('password') or '').strip() or hero_downloader.DEFAULT_PASSWORD
    vins_input = (data.get('vins') or data.get('vin') or '').strip()

    if not vins_input:
        return jsonify({'error': 'Please provide at least one VIN number.'}), 400

    vins = [v.strip().upper() for v in re.split(r'[\s,;]+', vins_input) if v.strip()]
    if not vins:
        return jsonify({'error': 'No valid VIN provided.'}), 400

    hypothecation = data.get('hypothecation', 'KEEP_ORIGINAL')
    new_date = data.get('new_date', '').strip()
    affix_stamp = str(data.get('affix_stamp', 'true')).lower() == 'true'
    scanned_look = str(data.get('scanned_look', 'true')).lower() == 'true'
    bw_mode = str(data.get('bw_mode', 'true')).lower() == 'true'
    headless = str(data.get('headless', 'true')).lower() == 'true'

    batch_token = str(uuid.uuid4())
    token_files = []
    converted_files = []

    try:
        results = hero_downloader.run_hero_automation_sync(
            vins=vins,
            username=user_id,
            password=password,
            download_dir=Path("HeroMotoCorp_Downloads"),
            output_dir=Path("output_invoices"),
            convert=True,
            hypothecation=hypothecation,
            new_date=new_date,
            affix_stamp=affix_stamp,
            scanned_effect=scanned_look,
            bw_mode=bw_mode,
            headless=headless
        )

        for r in results:
            vin = r["vin"]
            conv_dict = r.get("converted_files", {})
            for rep_name, cinfo in conv_dict.items():
                cpath = cinfo["converted_path"]
                if os.path.exists(cpath):
                    with open(cpath, 'rb') as cf:
                        pdf_bytes = cf.read()

                    file_id = str(uuid.uuid4())
                    fname = cinfo["filename"]
                    CONVERTED_STORE[file_id] = {
                        'filename': fname,
                        'data': pdf_bytes
                    }
                    token_files.append(file_id)
                    converted_files.append({
                        'id': file_id,
                        'vin': vin,
                        'report_name': rep_name,
                        'converted_name': fname,
                        'doc_type': cinfo.get('doc_type', 'invoice'),
                        'file_size_kb': cinfo.get('file_size_kb', round(len(pdf_bytes) / 1024.0, 1)),
                        'scanned_look': scanned_look,
                        'bw_mode': bw_mode
                    })

        if not converted_files:
            err_msg = "; ".join(r.get('error', '') for r in results if r.get('error')) or "No documents were retrieved or converted."
            return jsonify({'error': f"Failed to download/convert: {err_msg}"}), 500

        CONVERTED_STORE[batch_token] = token_files

        return jsonify({
            'token': batch_token,
            'files': converted_files
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/convert', methods=['POST'])
def api_convert():
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    uploaded_files = request.files.getlist('files')
    hypothecation = request.form.get('hypothecation', 'KEEP_ORIGINAL')
    new_date = request.form.get('new_date', '').strip()
    affix_stamp = request.form.get('affix_stamp', 'true').lower() == 'true'
    scanned_look = request.form.get('scanned_look', 'true').lower() == 'true'
    bw_mode = request.form.get('bw_mode', 'true').lower() == 'true'

    doc_mode = request.form.get('doc_mode', 'invoice')

    converted_files = []
    batch_token = str(uuid.uuid4())
    token_files = []

    temp_dir = tempfile.mkdtemp()

    for f in uploaded_files:
        if not f.filename.lower().endswith('.pdf'):
            continue

        safe_name = secure_filename(f.filename)
        in_path = os.path.join(temp_dir, f"in_{safe_name}")
        f.save(in_path)

        stem, ext = os.path.splitext(safe_name)
        converted_name = f"{stem}_annapurna{ext}"
        out_path = os.path.join(temp_dir, f"out_{converted_name}")

        try:
            mode_map = {
                'invoice': 'invoice',
                'sale-cert': 'sale_certificate',
                'form-22': 'form_22',
                'batch': None
            }
            target_doc_type = mode_map.get(doc_mode, None)

            stats = converter.convert_document(
                in_path,
                out_path,
                doc_type=target_doc_type,
                hypothecation=hypothecation,
                new_date=new_date,
                affix_stamp=affix_stamp,
                scanned_effect=scanned_look,
                bw_mode=bw_mode
            )

            file_id = str(uuid.uuid4())
            with open(out_path, 'rb') as out_f:
                pdf_bytes = out_f.read()

            file_size_kb = stats.get('file_size_kb', round(len(pdf_bytes) / 1024.0, 1))

            CONVERTED_STORE[file_id] = {
                'filename': converted_name,
                'data': pdf_bytes
            }
            token_files.append(file_id)

            converted_files.append({
                'id': file_id,
                'original_name': f.filename,
                'converted_name': converted_name,
                'doc_type': stats.get('doc_type', 'invoice'),
                'headers_replaced': stats.get('headers_replaced', 0),
                'footers_replaced': stats.get('footers_replaced', 0),
                'file_size_kb': file_size_kb,
                'scanned_look': scanned_look,
                'bw_mode': bw_mode
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    CONVERTED_STORE[batch_token] = token_files

    return jsonify({
        'token': batch_token,
        'files': converted_files
    })


@app.route('/api/download/<file_id>')
def download_file(file_id):
    item = CONVERTED_STORE.get(file_id)
    if not item:
        return "File not found", 404

    return send_file(
        io.BytesIO(item['data']),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=item['filename']
    )


@app.route('/api/preview/<file_id>')
def preview_file(file_id):
    item = CONVERTED_STORE.get(file_id)
    if not item:
        return "File not found", 404

    return send_file(
        io.BytesIO(item['data']),
        mimetype='application/pdf',
        as_attachment=False
    )


@app.route('/api/download-zip')
def download_zip():
    token = request.args.get('token')
    file_ids = CONVERTED_STORE.get(token)
    if not file_ids:
        return "Batch not found", 404

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for fid in file_ids:
            item = CONVERTED_STORE.get(fid)
            if item:
                zip_file.writestr(item['filename'], item['data'])

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='converted_annapurna_documents.zip'
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Hero MotoCorp Converter & Auto-Downloader at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
