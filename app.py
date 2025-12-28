from flask import Flask, render_template, request, redirect, url_for, jsonify
import os, json, threading, uuid
from datetime import datetime
from send_from_csv import run_send_job

app = Flask(__name__)

job_store = {}

def launch_send_in_thread(job_id, params):
    def logger(line):
        job_store[job_id]['logs'].append(line)

    job_store[job_id]['status'] = 'running'
    try:
        run_send_job(params, logger)
        job_store[job_id]['status'] = 'finished'
    except Exception as e:
        logger(f'Job error: {e}')
        job_store[job_id]['status'] = 'failed'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        # ✅ MUST EXIST
        edited_table = request.form.get('edited_table')
        if not edited_table:
            return "❌ No table data received", 400

        rows = json.loads(edited_table)

        # ------------------------------
        # Build messages list
        # ------------------------------
        messages = []
        i = 0
        while f'messages[{i}][text]' in request.form:
            messages.append({
                "template": request.form[f'messages[{i}][text]'],
                "send_datetime": request.form[f'messages[{i}][datetime]']
            })
            i += 1

        if not messages:
            return "❌ No messages configured", 400

        # ------------------------------
        # Write messages_db.json
        # ------------------------------
        with open('messages_db.json', 'w', encoding='utf-8') as f:
            json.dump({"web": messages}, f, indent=2)

        # ------------------------------
        # JOB PARAMS (NO CSV AT ALL)
        # ------------------------------
        params = {
            "edited_rows": rows,
            "messages_db": "messages_db.json",
            "template_key": "web",
            "name_col": 1,
            "phone_col": 2,
            "flag_col": 3,
            "country_code": "+91",
            "wait_time": 10
        }

        job_id = str(uuid.uuid4())
        job_store[job_id] = {"logs": [f"Job {job_id} created."], "status": "queued"}

        threading.Thread(
            target=launch_send_in_thread,
            args=(job_id, params),
            daemon=True
        ).start()

        return redirect(url_for('status_page', job_id=job_id))

    return render_template('index.html')


@app.route('/status/<job_id>')
def status_page(job_id):
    return render_template('status.html', job_id=job_id)


@app.route('/status/<job_id>/logs')
def status_logs(job_id):
    return jsonify(job_store.get(job_id, {}))


if __name__ == '__main__':
    app.run(debug=True)
