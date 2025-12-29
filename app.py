from flask import Flask, render_template, request, redirect, url_for, jsonify
import os, json, threading, uuid, csv
from datetime import datetime
from werkzeug.utils import secure_filename
from send_from_csv import run_send_job
import openpyxl

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

job_store = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_csv_file(filepath):
    """Parse CSV file and return headers + rows"""
    headers = []
    rows = []
    try:
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, [])
            
            for row in reader:
                if len(row) >= 2:  # At least Name and Phone
                    rows.append([cell.strip() for cell in row])
    except Exception as e:
        raise Exception(f"Error parsing CSV: {str(e)}")
    
    return headers, rows

def parse_xlsx_file(filepath):
    """Parse XLSX/XLS file and return headers + rows"""
    headers = []
    rows = []
    try:
        workbook = openpyxl.load_workbook(filepath)
        sheet = workbook.active
        
        if sheet is None:
            raise Exception("No active sheet found in workbook")
        
        # Get headers from first row
        headers = [str(cell.value).strip() if cell.value else f"Column{i}" 
                   for i, cell in enumerate(sheet[1], 1)]
        
        # Get data rows
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row and any(row):  # Skip empty rows
                row_data = [str(cell).strip() if cell is not None else '' for cell in row]
                if len(row_data) >= 2:  # At least Name and Phone
                    rows.append(row_data)
        
        workbook.close()
    except Exception as e:
        raise Exception(f"Error parsing XLSX: {str(e)}")
    
    return headers, rows

def launch_send_in_thread(job_id, params):
    def logger(line):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        job_store[job_id]['logs'].append(f"[{timestamp}] {line}")

    job_store[job_id]['status'] = 'running'
    job_store[job_id]['started_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        run_send_job(params, logger)
        job_store[job_id]['status'] = 'finished'
        job_store[job_id]['finished_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger(f'❌ Job error: {str(e)}')
        job_store[job_id]['status'] = 'failed'
        job_store[job_id]['error'] = str(e)


@app.route('/parse-excel', methods=['POST'])
def parse_excel():
    """Parse Excel/CSV file and return JSON data with headers"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"}), 400
        
        if file.filename is None:
            return jsonify({"success": False, "error": "Invalid filename"}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        try:
            if file_ext == 'csv':
                headers, rows = parse_csv_file(filepath)
            elif file_ext in ['xlsx', 'xls']:
                headers, rows = parse_xlsx_file(filepath)
            else:
                return jsonify({"success": False, "error": "Unsupported file type"}), 400
            
            os.remove(filepath)
            
            if not rows:
                return jsonify({"success": False, "error": "File is empty"}), 400
            
            # Validate that Name and Phone columns exist (prefer exact matches)
            name_col_idx = -1
            phone_col_idx = -1
            
            # First: Look for exact matches
            for idx, h in enumerate(headers):
                h_lower = h.lower().strip()
                if h_lower == 'name' and name_col_idx == -1:
                    name_col_idx = idx
                if h_lower == 'phone' and phone_col_idx == -1:
                    phone_col_idx = idx
            
            # Second: Look for partial matches if not found
            if name_col_idx == -1:
                for idx, h in enumerate(headers):
                    if 'name' in h.lower():
                        name_col_idx = idx
                        break
            
            if phone_col_idx == -1:
                for idx, h in enumerate(headers):
                    h_lower = h.lower()
                    if 'phone' in h_lower or 'mobile' in h_lower:
                        phone_col_idx = idx
                        break
            
            if name_col_idx == -1:
                return jsonify({"success": False, "error": "❌ Required column 'Name' not found in file headers"}), 400
            
            if phone_col_idx == -1:
                return jsonify({"success": False, "error": "❌ Required column 'Phone' not found in file headers"}), 400
            
            # Identify category columns (all columns except the detected Name and Phone)
            categories = []
            for idx, header in enumerate(headers):
                if idx != name_col_idx and idx != phone_col_idx:
                    categories.append(header)
            
            return jsonify({
                "success": True, 
                "headers": headers,
                "rows": rows,
                "categories": categories
            })
            
        except Exception as e:
            try:
                os.remove(filepath)
            except:
                pass
            return jsonify({"success": False, "error": f"Error parsing file: {str(e)}"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Get contact data
            edited_table = request.form.get('edited_table')
            if not edited_table:
                return jsonify({"error": "No contact data provided"}), 400
            
            contact_data = json.loads(edited_table)
            rows = contact_data.get('rows', [])
            headers = contact_data.get('headers', [])
            
            if not rows:
                return jsonify({"error": "No contacts provided"}), 400

            # Get filter-based message mappings
            filter_messages = []
            i = 0
            while f'filter_messages[{i}][filters]' in request.form:
                filters_json = request.form.get(f'filter_messages[{i}][filters]')
                message_text = request.form.get(f'filter_messages[{i}][message]', '').strip()
                datetime_val = request.form.get(f'filter_messages[{i}][datetime]', '').strip()
                
                if filters_json and message_text and datetime_val:
                    filter_messages.append({
                        "filters": json.loads(filters_json),
                        "template": message_text,
                        "send_datetime": datetime_val
                    })
                i += 1

            if not filter_messages:
                return jsonify({"error": "No message filters configured"}), 400

            # Write messages_db.json
            os.makedirs('data', exist_ok=True)
            messages_file = os.path.join('data', 'messages_db.json')
            with open(messages_file, 'w', encoding='utf-8') as f:
                json.dump({"filter_mappings": filter_messages}, f, indent=2, ensure_ascii=False)

            # Job parameters
            params = {
                "rows": rows,
                "headers": headers,
                "filter_messages": filter_messages,
                "messages_db": messages_file,
                "wait_time": int(request.form.get('wait_time', 10))
            }

            job_id = str(uuid.uuid4())
            job_store[job_id] = {
                "logs": [f"✅ Job {job_id} created with {len(rows)} contacts and {len(filter_messages)} message filters"],
                "status": "queued",
                "total_rows": len(rows),
                "total_filters": len(filter_messages),
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            threading.Thread(
                target=launch_send_in_thread,
                args=(job_id, params),
                daemon=True
            ).start()

            return jsonify({"success": True, "job_id": job_id})

        except json.JSONDecodeError as e:
            return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
        except Exception as e:
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    return render_template('index.html')


@app.route('/status/<job_id>')
def status_page(job_id):
    if job_id not in job_store:
        return "Job not found", 404
    return render_template('status.html', job_id=job_id)


@app.route('/status/<job_id>/logs')
def status_logs(job_id):
    return jsonify(job_store.get(job_id, {"error": "Job not found"}))


@app.route('/jobs')
def list_jobs():
    """List all jobs"""
    return jsonify({
        job_id: {
            "status": info["status"],
            "created_at": info.get("created_at"),
            "total_rows": info.get("total_rows", 0)
        }
        for job_id, info in job_store.items()
    })


@app.route('/preview-filter', methods=['POST'])
def preview_filter():
    """Preview which contacts match a specific filter"""
    try:
        data = request.json
        filters = data.get('filters', {})
        headers = data.get('headers', [])
        rows = data.get('rows', [])
        
        matched_contacts = []
        
        for row in rows:
            match = True
            for category, required_value in filters.items():
                col_idx = headers.index(category) if category in headers else -1
                if col_idx == -1 or col_idx >= len(row):
                    match = False
                    break
                
                cell_value = str(row[col_idx]).strip()
                if cell_value.upper() != required_value.upper():
                    match = False
                    break
            
            if match:
                matched_contacts.append({
                    'name': row[0] if len(row) > 0 else '',
                    'phone': row[1] if len(row) > 1 else ''
                })
        
        return jsonify({
            "success": True,
            "matched_count": len(matched_contacts),
            "matched_contacts": matched_contacts[:10],  # First 10 for preview
            "total_contacts": len(rows)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/duplicate-filter/<int:filter_id>', methods=['POST'])
def duplicate_filter():
    """Duplicate an existing filter configuration"""
    try:
        data = request.json
        return jsonify({"success": True, "message": "Filter duplicated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/export-config', methods=['POST'])
def export_config():
    """Export filter configuration as JSON for reuse"""
    try:
        data = request.json
        filter_messages = data.get('filter_messages', [])
        
        config = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "filters": filter_messages
        }
        
        return jsonify({
            "success": True,
            "config": config
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/import-config', methods=['POST'])
def import_config():
    """Import previously saved filter configuration"""
    try:
        config = request.json
        filters = config.get('filters', [])
        
        return jsonify({
            "success": True,
            "filters": filters
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/get-category-values', methods=['POST'])
def get_category_values():
    """Get unique values for a specific category column"""
    try:
        data = request.json
        category = data.get('category')
        headers = data.get('headers', [])
        rows = data.get('rows', [])
        
        if category not in headers:
            return jsonify({"success": False, "error": "Category not found"}), 400
        
        col_idx = headers.index(category)
        
        # Get unique non-empty values
        unique_values = sorted(list(set([
            str(row[col_idx]).strip() 
            for row in rows 
            if col_idx < len(row) and str(row[col_idx]).strip()
        ])))
        
        return jsonify({
            "success": True,
            "values": unique_values
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
