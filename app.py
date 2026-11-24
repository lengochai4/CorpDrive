from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
import sqlite3, subprocess, re, ipaddress

app = Flask(__name__)
app.secret_key = 'inse_demo_secret_key_2026'

def get_db():
    conn = sqlite3.connect('corpdrive.db')
    conn.row_factory = sqlite3.Row
    return conn

def log_action(action, target, status, note):
    db = get_db()
    db.execute('INSERT INTO activity_logs (username, action, target, status, note) VALUES (?, ?, ?, ?, ?)',
               (session.get('username', 'anonymous'), action, target, status, note))
    db.commit()

@app.route('/')
def index():
    return redirect(url_for('drive' if 'user_id' in session else 'login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        db = get_db()
        user = db.execute('SELECT * FROM employees WHERE username = ? AND password = ?',
                          (request.form['username'], request.form['password'])).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session.setdefault('mode', 'vulnerable')
            return redirect(url_for('drive'))
        error = 'Sai tên đăng nhập hoặc mật khẩu!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/toggle-mode', methods=['POST'])
def toggle_mode():
    current = session.get('mode', 'vulnerable')
    session['mode'] = 'secure' if current == 'vulnerable' else 'vulnerable'
    return redirect(request.referrer or url_for('drive'))

# --- 1. DEMO IDOR (ID ẨN TRONG JSON POST) ---
@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/api/profile', methods=['POST'])
def api_profile():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    target_id = int(data.get('user_id', 0))
    mode = session.get('mode', 'vulnerable')

    if mode == 'secure' and target_id != session['user_id']:
        log_action('POST /api/profile', f'user_id={target_id}', 'BLOCKED', 'IDOR Blocked: ID không khớp session hiện tại')
        return jsonify({'error': '403 Forbidden: Bạn chỉ được phép xem hồ sơ của chính mình!'}), 403

    db = get_db()
    user = db.execute('SELECT * FROM employees WHERE id = ?', (target_id,)).fetchone()
    if not user: return jsonify({'error': 'Không tìm thấy nhân viên'}), 404
    log_action('POST /api/profile', f'user_id={target_id}', 'ALLOWED', f'Xem hồ sơ của {user["username"]}')
    return jsonify(dict(user))

# --- 2. DEMO IDOR (ID LỘ THIÊN TRÊN URL & UUID) ---
@app.route('/drive')
def drive():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    docs = db.execute('SELECT * FROM documents WHERE owner_id = ?', (session['user_id'],)).fetchall()
    return render_template('drive.html', docs=docs)

@app.route('/drive/download')
def download_doc():
    if 'user_id' not in session: return redirect(url_for('login'))
    mode = session.get('mode', 'vulnerable')
    db = get_db()

    if mode == 'secure':
        doc_uuid = request.args.get('uuid', '')
        doc = db.execute('SELECT * FROM documents WHERE uuid = ?', (doc_uuid,)).fetchone()
        if not doc or doc['owner_id'] != session['user_id']:
            log_action('GET /drive/download', f'uuid={doc_uuid}', 'BLOCKED', 'IDOR Blocked: Sai UUID hoặc không phải chủ sở hữu')
            return "403 Forbidden: Truy cập tài liệu bị từ chối!", 403
    else:
        file_id = request.args.get('file_id', 0)
        doc = db.execute('SELECT * FROM documents WHERE id = ?', (file_id,)).fetchone()
        if not doc: return "404 Not Found", 404

    log_action('GET /drive/download', f'doc={doc["filename"]}', 'ALLOWED', f'Tải xuống tài liệu (owner_id={doc["owner_id"]})')
    return Response(doc['content'], mimetype='text/plain',
                    headers={'Content-Disposition': f'attachment; filename={doc["filename"]}'})

# --- 3. DEMO OS COMMAND INJECTION ---
@app.route('/network-check')
def network_check():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('ping.html')

@app.route('/api/ping', methods=['POST'])
def api_ping():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 401
    host = (request.get_json() or {}).get('host', '').strip()
    mode = session.get('mode', 'vulnerable')

    if mode == 'secure':
        is_valid = False
        try:
            ipaddress.ip_address(host)
            is_valid = True
        except ValueError:
            if re.match(r'^[a-zA-Z0-9.-]{1,253}$', host):
                is_valid = True
        if not is_valid:
            log_action('POST /api/ping', f'host={host}', 'BLOCKED', 'Command Injection Blocked: Ký tự đặc biệt không hợp lệ')
            return jsonify({'error': '400 Bad Request: Địa chỉ IP/Hostname không hợp lệ!'}), 400

        res = subprocess.run(['ping', '-n', '2', host], shell=False, capture_output=True, text=True)
        log_action('POST /api/ping', f'host={host}', 'ALLOWED', 'Ping an toàn (shell=False)')
        return jsonify({'output': res.stdout or res.stderr})

    # VULNERABLE MODE: Nối chuỗi trực tiếp vào shell
    res = subprocess.run(f'ping -n 2 {host}', shell=True, capture_output=True, text=True)
    log_action('POST /api/ping', f'host={host}', 'ALLOWED', 'Thực thi lệnh shell trực tiếp (shell=True)')
    return jsonify({'output': res.stdout or res.stderr})

@app.route('/logs')
def logs():
    if 'user_id' not in session: return redirect(url_for('login'))
    db = get_db()
    rows = db.execute('SELECT * FROM activity_logs ORDER BY id DESC LIMIT 100').fetchall()
    return render_template('logs.html', logs=rows)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)