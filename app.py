#!/usr/bin/env python3
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os.path

app = Flask(__name__)
app.secret_key = 'kit-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

DATABASE = 'kit.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'nowe',
            admin_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users(id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            role_required TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'oczekujące',
            time_estimated REAL,
            time_actual REAL,
            completed_by INTEGER,
            completed_at TIMESTAMP,
            step_order INTEGER DEFAULT 0,
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (completed_by) REFERENCES users(id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_id INTEGER,
            task_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            uploaded_by INTEGER,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (step_id) REFERENCES process_steps(id),
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT
        )
        ''')
        
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('admin', 'Administrator')")
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('user', 'Użytkownik')")
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('konstruktor', 'Konstruktor')")
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('technolog', 'Technolog')")
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('wdrozeniowiec', 'Wdrożeniowiec')")
        
        admin_exists = cursor.execute("SELECT id FROM users WHERE role='admin'").fetchone()
        if not admin_exists:
            cursor.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                         ('admin', generate_password_hash('admin123'), 'admin', 'Administrator'))
        
        db.commit()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Brak uprawnień administratora')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    db = get_db()
    user_role = session.get('role')
    
    if user_role == 'admin':
        tasks = db.execute('SELECT t.*, u.username as admin_name FROM tasks t LEFT JOIN users u ON t.admin_id = u.id ORDER BY t.created_at DESC').fetchall()
        users = db.execute('SELECT * FROM users WHERE role != "admin"').fetchall()
        return render_template('admin_dashboard.html', tasks=tasks, users=users)
    else:
        tasks = db.execute('''
            SELECT DISTINCT t.*, 
                   (SELECT COUNT(*) FROM process_steps WHERE task_id = t.id) as total_steps,
                   (SELECT COUNT(*) FROM process_steps WHERE task_id = t.id AND status = 'zakończone') as completed_steps
            FROM tasks t
            JOIN process_steps ps ON t.id = ps.task_id
            WHERE ps.role_required = ? OR ? = 'admin'
            ORDER BY t.created_at DESC
        ''', (user_role, user_role)).fetchall()
        return render_template('user_dashboard.html', tasks=tasks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            return redirect(url_for('index'))
        else:
            flash('Nieprawidłowy login lub hasło')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    db = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            full_name = request.form.get('full_name', '')
            
            try:
                db.execute('INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)',
                         (username, generate_password_hash(password), role, full_name))
                db.commit()
                flash('Użytkownik dodany pomyślnie')
            except sqlite3.IntegrityError:
                flash('Użytkownik o tej nazwie już istnieje')
        
        elif action == 'delete':
            user_id = request.form['user_id']
            if user_id != str(session['user_id']):
                db.execute('DELETE FROM users WHERE id = ? AND role != "admin"', (user_id,))
                db.commit()
                flash('Użytkownik usunięty')
    
    users = db.execute('SELECT * FROM users WHERE role != "admin" ORDER BY username').fetchall()
    return render_template('manage_users.html', users=users)

@app.route('/admin/tasks/new', methods=['GET', 'POST'])
@admin_required
def new_task():
    db = get_db()
    
    if request.method == 'POST':
        project_name = request.form['project_name']
        description = request.form.get('description', '')
        
        cursor = db.execute('INSERT INTO tasks (project_name, description, admin_id) VALUES (?, ?, ?)',
                          (project_name, description, session['user_id']))
        task_id = cursor.lastrowid
        
        steps = [
            ('konstruktor', 'Przygotowanie rysunku ilustracji', 1),
            ('konstruktor', 'Przygotowanie rysunku do kroju (DXF/DWG)', 2),
            ('technolog', 'Opracowanie BOM (Arkusz: Elementy)', 3),
            ('technolog', 'Lista procesów z czasami', 4),
            ('wdrozeniowiec', 'Przygotowanie instrukcji krok po kroku', 5)
        ]
        
        for role, desc, order in steps:
            db.execute('INSERT INTO process_steps (task_id, role_required, description, step_order) VALUES (?, ?, ?, ?)',
                     (task_id, role, desc, order))
        
        db.commit()
        flash('Zadanie utworzone pomyślnie')
        return redirect(url_for('index'))
    
    return render_template('new_task.html')

@app.route('/uploads/<filename>')
@login_required
def serve_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    flash('Plik nie istnieje')
    return redirect(url_for('index'))

@app.route('/task/<int:task_id>/upload', methods=['POST'])
@login_required
def upload_file(task_id):
    if 'file' not in request.files:
        flash('Brak pliku')
        return redirect(url_for('view_task', task_id=task_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('Nie wybrano pliku')
        return redirect(url_for('view_task', task_id=task_id))
    
    db = get_db()
    step_id = request.form.get('step_id') or None
    
    filename = f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    db.execute('INSERT INTO files (task_id, step_id, filename, file_path, file_type, uploaded_by) VALUES (?, ?, ?, ?, ?, ?)',
              (task_id, step_id, filename, filepath, file.content_type, session['user_id']))
    db.commit()
    
    flash('Plik wysłany')
    return redirect(url_for('view_task', task_id=task_id))

@app.route('/task/<int:task_id>')
@login_required
def view_task(task_id):
    db = get_db()
    task = db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    
    if not task:
        flash('Zadanie nie istnieje')
        return redirect(url_for('index'))
    
    steps = db.execute('SELECT * FROM process_steps WHERE task_id = ? ORDER BY step_order', (task_id,)).fetchall()
    files = db.execute('SELECT f.*, u.username FROM files f LEFT JOIN users u ON f.uploaded_by = u.id WHERE f.task_id = ?', (task_id,)).fetchall()
    
    return render_template('view_task.html', task=task, steps=steps, files=files)

@app.route('/task/<int:task_id>/step/<int:step_id>/complete', methods=['POST'])
@login_required
def complete_step(task_id, step_id):
    db = get_db()
    user_role = session.get('role')
    
    step = db.execute('SELECT * FROM process_steps WHERE id = ? AND task_id = ?', (step_id, task_id)).fetchone()
    
    if step['role_required'] != user_role:
        flash('To zadanie nie jest przypisane do Twojej roli')
        return redirect(url_for('view_task', task_id=task_id))
    
    if step['status'] == 'zakończone':
        flash('Ten krok został już zakończony')
        return redirect(url_for('view_task', task_id=task_id))
    
    time_actual = request.form.get('time_actual')
    
    db.execute('UPDATE process_steps SET status = ?, completed_by = ?, completed_at = ?, time_actual = ? WHERE id = ?',
             ('zakończone', session['user_id'], datetime.now(), time_actual, step_id))
    
    all_steps = db.execute('SELECT COUNT(*) as total, SUM(CASE WHEN status = "zakończone" THEN 1 ELSE 0 END) as completed FROM process_steps WHERE task_id = ?', (task_id,)).fetchone()
    
    if all_steps['total'] == all_steps['completed']:
        db.execute('UPDATE tasks SET status = ? WHERE id = ?', ('zakończone', task_id))
    
    db.commit()
    flash('Krok zakończony')
    return redirect(url_for('view_task', task_id=task_id))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
