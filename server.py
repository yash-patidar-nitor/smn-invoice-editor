"""
Hero Invoice Converter - Web Application Server
Flask-based responsive web app with drag-and-drop conversion,
live PDF preview, batch processing, and ZIP download.
"""

import os
import io
import zipfile
import tempfile
from flask import Flask, request, jsonify, send_file, render_template_string
from werkzeug.utils import secure_filename
import converter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB max upload

CONVERTED_STORE = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hero Invoice Converter - Shanti to Annapurna</title>
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
        body { background: var(--bg-color); color: var(--text-dark); padding: 24px 16px; min-height: 100vh; }
        .container { max-width: 820px; margin: 0 auto; }
        
        .header { margin-bottom: 24px; text-align: center; }
        .badge { display: inline-block; padding: 4px 12px; background: #dbeafe; color: var(--primary); font-size: 12px; font-weight: 600; border-radius: 9999px; margin-bottom: 8px; }
        .title { font-size: 28px; font-weight: 700; color: var(--text-dark); letter-spacing: -0.5px; }
        .subtitle { color: var(--text-muted); font-size: 14px; margin-top: 4px; }
        
        .card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
        .card-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; color: var(--text-dark); display: flex; align-items: center; gap: 8px; }

        .mode-selector { display: flex; gap: 12px; }
        .mode-option { flex: 1; border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; cursor: pointer; transition: all 0.2s; text-align: center; font-size: 13px; font-weight: 500; }
        .mode-option:hover { border-color: var(--primary); }
        .mode-option.active { border-color: var(--primary); background: #eff6ff; color: var(--primary); font-weight: 600; }

        .drop-zone { border: 2px dashed #cbd5e1; border-radius: var(--radius); padding: 36px 20px; text-align: center; cursor: pointer; transition: all 0.2s; background: #f8fafc; }
        .drop-zone:hover, .drop-zone.dragover { border-color: var(--primary); background: #eff6ff; }
        .drop-zone-icon { font-size: 36px; margin-bottom: 8px; }
        .drop-zone-title { font-size: 15px; font-weight: 600; color: var(--text-dark); }
        .drop-zone-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
        
        .file-list { margin-top: 14px; display: none; }
        .file-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: #f1f5f9; border-radius: 8px; margin-bottom: 6px; font-size: 13px; }
        .file-name { font-weight: 500; color: var(--text-dark); }
        .file-size { color: var(--text-muted); font-size: 12px; }
        .file-remove { color: #ef4444; cursor: pointer; font-weight: 600; padding: 2px 6px; }

        .btn-convert { width: 100%; background: var(--primary); color: #fff; border: none; padding: 14px; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.2s; margin-top: 10px; display: flex; align-items: center; justify-content: center; gap: 8px; }
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

        .result-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 6px; font-size: 13px; background: #fff; }
        .result-actions { display: flex; gap: 8px; }
        .btn-link { font-size: 12px; font-weight: 600; text-decoration: none; padding: 4px 10px; border-radius: 4px; }
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
            <span class="badge">Hero MotoCorp Dealership Tool</span>
            <h1 class="title">Invoice Converter</h1>
            <p class="subtitle">Convert Shanti Motors invoices into official Annapurna Motors format</p>
        </div>

        <div class="card">
            <div class="card-title">1. Conversion Mode</div>
            <div class="mode-selector">
                <div class="mode-option active" id="mode-shanti-ann" onclick="setMode('shanti_to_annapurna')">
                    Shanti Motors ➔ Annapurna Motors
                </div>
                <div class="mode-option" id="mode-ann-shanti" onclick="setMode('annapurna_to_shanti')">
                    Annapurna Motors ➔ Shanti Motors (Reverse)
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">2. Upload Invoices</div>
            <div class="drop-zone" id="drop-zone" onclick="document.getElementById('file-input').click()">
                <div class="drop-zone-icon">📄</div>
                <div class="drop-zone-title">Click to upload or drag & drop PDF invoices</div>
                <div class="drop-zone-desc">Supports single or batch Hero MotoCorp tax invoice PDFs</div>
                <input type="file" id="file-input" multiple accept=".pdf" style="display:none" onchange="handleFileSelect(event)">
            </div>

            <div class="file-list" id="file-list"></div>

            <button class="btn-convert" id="btn-convert" onclick="startConversion()" disabled>
                ⚡ Convert Invoices
            </button>

            <div class="progress-box" id="progress-box">
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" id="progress-fill"></div>
                </div>
                <div class="progress-status" id="progress-status">Processing...</div>
            </div>
        </div>

        <div class="card results-box" id="results-box">
            <div class="card-title">3. Converted Invoices</div>
            <div class="success-banner">
                <div class="success-text" id="success-summary">All files converted successfully!</div>
                <a href="#" class="btn-download-all" id="btn-download-all">📦 Download All as ZIP</a>
            </div>
            <div id="results-list"></div>
        </div>
    </div>

    <!-- Preview Modal -->
    <div class="preview-modal" id="preview-modal">
        <div class="preview-content">
            <div class="preview-header">
                <div class="preview-title" id="preview-filename">Converted Invoice Preview</div>
                <button class="preview-close" onclick="closePreview()">&times;</button>
            </div>
            <iframe class="preview-iframe" id="preview-iframe"></iframe>
        </div>
    </div>

    <script>
        let selectedFiles = [];
        let currentMode = 'shanti_to_annapurna';

        function setMode(mode) {
            currentMode = mode;
            document.getElementById('mode-shanti-ann').classList.toggle('active', mode === 'shanti_to_annapurna');
            document.getElementById('mode-ann-shanti').classList.toggle('active', mode === 'annapurna_to_shanti');
        }

        const dropZone = document.getElementById('drop-zone');
        ['dragenter', 'dragover'].forEach(name => {
            dropZone.addEventListener(name, (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
        });
        ['dragleave', 'drop'].forEach(name => {
            dropZone.addEventListener(name, (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); });
        });
        dropZone.addEventListener('drop', (e) => {
            if (e.dataTransfer.files) {
                addFiles(Array.from(e.dataTransfer.files));
            }
        });

        function handleFileSelect(e) {
            if (e.target.files) {
                addFiles(Array.from(e.target.files));
            }
        }

        function addFiles(files) {
            const pdfs = files.filter(f => f.name.toLowerCase().endsWith('.pdf'));
            pdfs.forEach(f => {
                if (!selectedFiles.some(existing => existing.name === f.name)) {
                    selectedFiles.push(f);
                }
            });
            renderFileList();
        }

        function removeFile(index) {
            selectedFiles.splice(index, 1);
            renderFileList();
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
            list.style.display = 'block';
            btn.disabled = false;
            list.innerHTML = selectedFiles.map((f, i) => `
                <div class="file-item">
                    <div>
                        <span class="file-name">${f.name}</span>
                        <span class="file-size">(${(f.size / 1024).toFixed(1)} KB)</span>
                    </div>
                    <span class="file-remove" onclick="removeFile(${i})">&times; Remove</span>
                </div>
            `).join('');
        }

        async function startConversion() {
            if (selectedFiles.length === 0) return;

            const btn = document.getElementById('btn-convert');
            const progressBox = document.getElementById('progress-box');
            const progressFill = document.getElementById('progress-fill');
            const progressStatus = document.getElementById('progress-status');
            const resultsBox = document.getElementById('results-box');

            btn.disabled = true;
            progressBox.style.display = 'block';
            resultsBox.style.display = 'none';
            progressFill.style.width = '30%';
            progressStatus.innerText = 'Uploading and processing invoices...';

            const formData = new FormData();
            formData.append('direction', currentMode);
            selectedFiles.forEach(f => formData.append('files', f));

            try {
                const response = await fetch('/api/convert', { method: 'POST', body: formData });
                progressFill.style.width = '80%';
                
                if (!response.ok) {
                    throw new Error('Conversion failed on server');
                }

                const data = await response.json();
                progressFill.style.width = '100%';
                progressStatus.innerText = 'Conversion completed!';

                renderResults(data);
            } catch (err) {
                progressStatus.innerText = 'Error: ' + err.message;
            } finally {
                btn.disabled = false;
            }
        }

        function renderResults(data) {
            const resultsBox = document.getElementById('results-box');
            const summary = document.getElementById('success-summary');
            const btnZip = document.getElementById('btn-download-all');
            const list = document.getElementById('results-list');

            resultsBox.style.display = 'block';
            summary.innerText = `Converted ${data.files.length} invoice(s) successfully!`;
            btnZip.href = `/api/download-zip?token=${data.token}`;
            btnZip.style.display = data.files.length > 1 ? 'inline-flex' : 'none';

            list.innerHTML = data.files.map(f => `
                <div class="result-item">
                    <div>
                        <strong>${f.converted_name}</strong>
                        <div style="font-size: 11px; color: var(--text-muted);">
                            Headers replaced: ${f.headers_replaced} | Signatory replaced: ${f.footers_replaced}
                        </div>
                    </div>
                    <div class="result-actions">
                        <button class="btn-link btn-preview" onclick="openPreview('${f.id}', '${f.converted_name}')">👁 Preview</button>
                        <a href="/api/download/${f.id}" class="btn-link btn-download">⬇ Download</a>
                    </div>
                </div>
            `).join('');
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
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/convert', methods=['POST'])
def api_convert():
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    uploaded_files = request.files.getlist('files')
    direction = request.form.get('direction', 'shanti_to_annapurna')

    converted_files = []
    import uuid
    batch_token = str(uuid.uuid4())
    token_files = []

    temp_dir = tempfile.mkdtemp()

    for f in uploaded_files:
        if not f.filename.lower().endswith('.pdf'):
            continue

        safe_name = secure_filename(f.filename)
        in_path = os.path.join(temp_dir, f"in_{safe_name}")
        f.save(in_path)

        prefix = "annapurna_" if direction == "shanti_to_annapurna" else "shanti_"
        converted_name = f"{prefix}{safe_name}"
        out_path = os.path.join(temp_dir, f"out_{safe_name}")

        try:
            if direction == "shanti_to_annapurna":
                stats = converter.convert_shanti_to_annapurna(in_path, out_path)
            else:
                stats = converter.convert_annapurna_to_shanti(in_path, out_path)

            file_id = str(uuid.uuid4())
            with open(out_path, 'rb') as out_f:
                pdf_bytes = out_f.read()

            CONVERTED_STORE[file_id] = {
                'filename': converted_name,
                'data': pdf_bytes
            }
            token_files.append(file_id)

            converted_files.append({
                'id': file_id,
                'original_name': f.filename,
                'converted_name': converted_name,
                'headers_replaced': stats.get('headers_replaced', 0),
                'footers_replaced': stats.get('footers_replaced', 0)
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
        download_name='converted_annapurna_invoices.zip'
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Hero Invoice Converter Web App at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
