from flask import Flask, render_template, request, redirect, url_for, jsonify
import os, json, threading, uuid, csv
from datetime import datetime
from werkzeug.utils import secure_filename
from send_from_csv import run_send_job

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

job_store = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_csv_file(filepath):
    """Parse CSV file and return rows"""
    rows = []
    try:
        with open(filepath, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            # Skip header if exists
            header = next(reader, None)
            
            for row in reader:
                if len(row) >= 3:  # Need at least name, phone, flag
                    # Phone can include country code (e.g., +1234567890 or 1234567890)
                    phone = row[1].strip()
                    
                    rows.append([
                        row[0].strip(),  # Name
                        phone,           # Phone (with country code if provided)
                        row[2].strip()   # Flag (0 or 1)
                    ])
    except Exception as e:
        raise Exception(f"Error parsing CSV: {str(e)}")
    
    return rows

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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            rows = []
            
            # Check for edited table data (from both CSV and manual entry)
            edited_table = request.form.get('edited_table')
            if edited_table:
                rows = json.loads(edited_table)
                
                if not rows or len(rows) == 0:
                    return jsonify({"error": "No contact data provided"}), 400
            else:
                # Fallback: Check if CSV file was uploaded (old flow)
                if 'csv_file' in request.files:
                    file = request.files['csv_file']
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        
                        # Parse CSV file
                        rows = parse_csv_file(filepath)
                        
                        if not rows or len(rows) == 0:
                            return jsonify({"error": "CSV file is empty or invalid"}), 400
                else:
                    return jsonify({"error": "No contact data provided"}), 400

            # Build messages list
            messages = []
            i = 0
            while f'messages[{i}][text]' in request.form:
                msg_text = request.form.get(f'messages[{i}][text]', '').strip()
                msg_datetime = request.form.get(f'messages[{i}][datetime]', '').strip()
                
                if msg_text and msg_datetime:
                    messages.append({
                        "template": msg_text,
                        "send_datetime": msg_datetime
                    })
                i += 1

            if not messages:
                return jsonify({"error": "No messages configured"}), 400

            # Write messages_db.json
            os.makedirs('data', exist_ok=True)
            messages_file = os.path.join('data', 'messages_db.json')
            with open(messages_file, 'w', encoding='utf-8') as f:
                json.dump({"web": messages}, f, indent=2, ensure_ascii=False)

            # Job parameters
            params = {
                "edited_rows": rows,
                "messages_db": messages_file,
                "template_key": "web",
                "name_col": 0,
                "phone_col": 1,
                "flag_col": 2,
                "country_code": '',  # No default country code
                "wait_time": int(request.form.get('wait_time', 10)),
                "use_country_code": False  # Always use phone numbers as-is
            }

            job_id = str(uuid.uuid4())
            job_store[job_id] = {
                "logs": [f"✅ Job {job_id} created with {len(rows)} contacts"],
                "status": "queued",
                "total_rows": len(rows),
                "total_messages": len(messages),
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            threading.Thread(
                target=launch_send_in_thread,
                args=(job_id, params),
                daemon=True
            ).start()

            return jsonify({"success": True, "job_id": job_id})

        except json.JSONDecodeError:
            return jsonify({"error": "Invalid data format"}), 400
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
