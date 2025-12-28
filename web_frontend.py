from flask import Flask, render_template, request, redirect, url_for
import os
import json
import threading
import subprocess
import sys
from datetime import datetime
import uuid
from flask import jsonify
from send_from_csv import run_send_job

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

MESSAGES_DB = os.path.join(os.path.dirname(__file__), 'messages_db.json')


job_store = {}


def launch_send_in_thread(job_id, csv_path, params):
    def logger(line):
        job_store[job_id]['logs'].append(line)
    job_store[job_id]['status'] = 'running'
    try:
        params_local = params.copy()
        params_local['csv'] = csv_path
        run_send_job(params_local, logger)
        job_store[job_id]['status'] = 'finished'
    except Exception as e:
        job_store[job_id]['logs'].append(f'Job error: {e}')
        job_store[job_id]['status'] = 'failed'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # get form data
        message = request.form.get('message')
        send_dt = request.form.get('send_datetime')  # format: YYYY-MM-DDTHH:MM
        uploaded = request.files.get('csvfile')

        if not uploaded or uploaded.filename == '':
            return "No CSV uploaded", 400

        filename = uploaded.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded.save(save_path)

        # write messages_db.json with key 'web'
        entry = {'template': message, 'send_datetime': None, 'send_time': None}
        if send_dt:
            try:
                dt = datetime.fromisoformat(send_dt)
                entry['send_datetime'] = dt.isoformat(sep=' ')
            except Exception:
                entry['send_datetime'] = send_dt

        db = {}
        if os.path.exists(MESSAGES_DB):
            try:
                with open(MESSAGES_DB, 'r', encoding='utf-8') as f:
                    db = json.load(f)
            except Exception:
                db = {}
        db['web'] = entry
        with open(MESSAGES_DB, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)

        # prepare params for run_send_job (job will read message & timing from messages_db)
        params = {
            'name_col': 1,
            'phone_col': 2,
            'flag_col': 3,
            'country_code': '+91',
            'wait_time': 10,
            'keep_tab': False,
            'messages_db': MESSAGES_DB,
            'template_key': 'web',
            'datetime_col': None,
            'date_col': None,
            'time_col': None,
            'default_send_datetime': entry.get('send_datetime'),
            'default_send_time': entry.get('send_time'),
        }

        job_id = str(uuid.uuid4())
        job_store[job_id] = {'logs': [f'Job {job_id} created.'], 'status': 'queued'}
        threading.Thread(target=launch_send_in_thread, args=(job_id, save_path, params), daemon=True).start()

        return redirect(url_for('status_page', job_id=job_id))

    return render_template('index.html')


@app.route('/map/<filename>', methods=['GET'])
def map_columns(filename):
    # not used now; placeholder for future mapping UI
    return f'Mapping for {filename}'


@app.route('/status/<job_id>')
def status_page(job_id):
    if job_id not in job_store:
        return 'Job not found', 404
    return render_template('status.html', job_id=job_id)


@app.route('/status/<job_id>/logs')
def status_logs(job_id):
    if job_id not in job_store:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'status': job_store[job_id]['status'], 'logs': job_store[job_id]['logs']})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
