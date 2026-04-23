#!/usr/bin/env python3
"""
Aplikacja KIT (Konstrukcja i Technologia) - System zarządzania pracami w dziale KiT
==============================================================================
Aplikacja webowa działająca w sieci lokalnej LAN z wbudowaną bazą danych SQLite.
Obsługuje dwa tryby pracy: użytkownik i administrator.

Główne funkcjonalności:
- System logowania z podziałem na role (admin, konstruktor, technolog, wdrożeniowiec)
- Zarządzanie zadaniami i przepływem pracy (workflow)
- Automatyczne tworzenie kroków procesu dla nowych zadań
- Przesyłanie i pobieranie plików (rysunki, BOM, instrukcje)
- Śledzenie postępu zadań poprzez pasek postępu
- Panel administratora do zarządzania użytkownikami
"""

# Import modułów standardowych
import os
import sqlite3

# Import modułów Flask - framework webowy do obsługi żądań HTTP
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, send_file

# Import funkcji do bezpiecznego haszowania haseł
from werkzeug.security import generate_password_hash, check_password_hash

# Import dekoratora wraps do zachowania metadanych funkcji
from functools import wraps

# Import klasy datetime do operacji na datach i czasie
from datetime import datetime

# Import modułu os.path do operacji na ścieżkach plików
import os.path

# Inicjalizacja aplikacji Flask
app = Flask(__name__)

# Klucz sekretny używany do podpisywania ciasteczek sesji (bezpieczeństwo)
app.secret_key = 'kit-secret-key-2024'

# Katalog, w którym będą przechowywane wgrane pliki (rysunki, dokumenty)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Maksymalny rozmiar przesyłanego pliku: 16MB (zabezpieczenie przed przeciążeniem)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Nazwa pliku bazy danych SQLite (będzie utworzony w katalogu projektu)
DATABASE = 'kit.db'

def get_db():
    """
    Funkcja pomocnicza do obsługi połączenia z bazą danych SQLite.
    Wykorzystuje obiekt 'g' Flask do przechowywania połączenia w ramach jednego żądania.
    Dzięki temu wielokrotne wywołania get_db() w jednym żądaniu używają tego samego połączenia.
    
    Zwraca:
        sqlite3.Connection: Obiekt połączenia z bazą danych
    """
    # Sprawdź czy połączenie już istnieje w kontekście 'g' (obiekt Flask dla danego żądania)
    db = getattr(g, '_database', None)
    if db is None:
        # Utwórz nowe połączenie z bazą i zapisz w kontekście 'g'
        db = g._database = sqlite3.connect(DATABASE)
        # Ustaw row_factory na sqlite3.Row - pozwala to na dostęp do kolumn po nazwie (jak w słowniku)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """
    Funkcja wywoływana automatycznie przez Flask po zakończeniu każdego żądania.
    Zamyka połączenie z bazą danych, jeśli było otwarte.
    Dekorator @app.teardown_appcontext rejestruje tę funkcję jako callback.
    """
    # Pobierz połączenie z kontekstu 'g'
    db = getattr(g, '_database', None)
    if db is not None:
        # Zamknij połączenie z bazą danych
        db.close()

def init_db():
    """
    Inicjalizacja bazy danych - tworzenie wszystkich wymaganych tabel.
    Funkcja sprawdza czy tabele istnieją (CREATE TABLE IF NOT EXISTS)
    i tworzy domyślne role oraz konta administratorów.
    
    Tablice:
    - users: przechowuje dane użytkowników (login, hasło, rola)
    - tasks: przechowuje zadania/projekty
    - process_steps: kroki procesu dla każdego zadania
    - files: pliki powiązane z zadaniami
    - roles: lista dostępnych ról w systemie
    """
    # Użyj kontekstu aplikacji Flask (wymagane do dostępu do bazy poza żądaniem)
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Tabela użytkowników - przechowuje dane logowania i role
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
        
        # Tabela zadań (projektów) - tworzone przez administratora
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
        
        # Tabela kroków procesu - automatycznie generowana dla każdego zadania
        # Każdy krok ma przypisaną rolę, która może go wykonać
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
        
        # Tabela plików - przechowuje informacje o wgranych plikach
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
        
        # Tabela ról - słownik dostępnych ról w systemie
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT
        )
        ''')
        
        # Wstawienie domyślnych ról (jeśli jeszcze nie istnieją)
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('admin', 'Administrator')")
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('user', 'Użytkownik')")
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('konstruktor', 'Konstruktor')")
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('technolog', 'Technolog')")
        cursor.execute("INSERT OR IGNORE INTO roles (name, display_name) VALUES ('wdrozeniowiec', 'Wdrożeniowiec')")
        
        # Sprawdź czy istnieje już jakiś administrator
        admin_exists = cursor.execute("SELECT id FROM users WHERE role='admin'").fetchone()
        if not admin_exists:
            # Utwórz domyślne konto administratora (login: admin, hasło: admin123)
            cursor.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                         ('admin', generate_password_hash('admin123'), 'admin', 'Administrator'))
        
        # Zatwierdź zmiany w bazie danych
        db.commit()

def login_required(f):
    """
    Dekorator sprawdzający czy użytkownik jest zalogowany.
    Jeśli w sesji nie ma 'user_id', przekierowuje na stronę logowania.
    Używa funkcji wraps z modułu functools, aby zachować metadane oryginalnej funkcji.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Sprawdź czy użytkownik jest zalogowany (ma user_id w sesji)
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Dekorator sprawdzający czy zalogowany użytkownik ma rolę administratora.
    Jeśli nie - wyświetla komunikat o braku uprawnień i przekierowuje na stronę główną.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Sprawdź czy użytkownik jest zalogowany i czy ma rolę 'admin'
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Brak uprawnień administratora')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def index():
    """
    Główna strona aplikacji - dashboard użytkownika lub administratora.
    Po zalogowaniu użytkownik widzi swoje zadania, administrator widzi wszystkie zadania i użytkowników.
    """
    db = get_db()
    user_role = session.get('role')
    
    # Dla administratora - pokaż wszystkie zadania i listę użytkowników
    if user_role == 'admin':
        # Pobierz wszystkie zadania wraz z nazwą administratora, który je utworzył
        tasks = db.execute('SELECT t.*, u.username as admin_name FROM tasks t LEFT JOIN users u ON t.admin_id = u.id ORDER BY t.created_at DESC').fetchall()
        # Pobierz wszystkich użytkowników (poza administratorami)
        users = db.execute('SELECT * FROM users WHERE role != "admin"').fetchall()
        return render_template('admin_dashboard.html', tasks=tasks, users=users)
    else:
        # Dla zwykłego użytkownika - pokaż tylko zadania przypisane do jego roli
        # Oblicz też liczbę wszystkich kroków i ukończonych kroków dla każdego zadania
        # Sprawdzamy czy rola użytkownika znajduje się w kolumnie role_required (może zawierać wiele ról oddzielonych przecinkiem)
        tasks = db.execute('''
            SELECT DISTINCT t.*, 
                   (SELECT COUNT(*) FROM process_steps WHERE task_id = t.id) as total_steps,
                   (SELECT COUNT(*) FROM process_steps WHERE task_id = t.id AND status = 'zakończone') as completed_steps
            FROM tasks t
            JOIN process_steps ps ON t.id = ps.task_id
            WHERE (',' || ps.role_required || ',' LIKE '%,' || ? || ',%') OR ? = 'admin'
            ORDER BY t.created_at DESC
        ''', (user_role, user_role)).fetchall()
        return render_template('user_dashboard.html', tasks=tasks)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Strona logowania - obsługa formularza logowania.
    GET: Wyświetla formularz logowania
    POST: Sprawdza dane logowania i tworzy sesję użytkownika
    """
    if request.method == 'POST':
        # Pobierz dane z formularza
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        # Sprawdź czy użytkownik istnieje w bazie
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        # Sprawdź czy hasło jest poprawne (weryfikacja hasha)
        if user and check_password_hash(user['password_hash'], password):
            # Zapisz dane użytkownika w sesji
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            return redirect(url_for('index'))
        else:
            flash('Nieprawidłowy login lub hasło')
    
    # Wyświetl formularz logowania (GET) lub po błędzie logowania
    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    Wylogowanie użytkownika - czyści wszystkie dane z sesji
    i przekierowuje na stronę logowania.
    """
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    """
    Panel zarządzania użytkownikami (tylko dla administratora).
    GET: Wyświetla listę użytkowników i formularz dodawania
    POST: Obsługuje akcje dodawania i usuwania użytkowników
    """
    db = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Akcja dodawania nowego użytkownika
        if action == 'add':
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            full_name = request.form.get('full_name', '')
            
            try:
                # Wstaw nowego użytkownika do bazy (hasło jest haszowane)
                db.execute('INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)',
                         (username, generate_password_hash(password), role, full_name))
                db.commit()
                flash('Użytkownik dodany pomyślnie')
            except sqlite3.IntegrityError:
                # Użytkownik o tej nazwie już istnieje (naruszenie UNIQUE)
                flash('Użytkownik o tej nazwie już istnieje')
        
        # Akcja usuwania użytkownika
        elif action == 'delete':
            user_id = request.form['user_id']
            # Nie pozwól usunąć samego siebie
            if user_id != str(session['user_id']):
                # Usuń tylko jeśli to nie jest administrator
                db.execute('DELETE FROM users WHERE id = ? AND role != "admin"', (user_id,))
                db.commit()
                flash('Użytkownik usunięty')
    
    # Pobierz listę użytkowników (poza administratorami) posortowaną alfabetycznie
    users = db.execute('SELECT * FROM users WHERE role != "admin" ORDER BY username').fetchall()
    return render_template('manage_users.html', users=users)

@app.route('/admin/tasks/new', methods=['GET', 'POST'])
@admin_required
def new_task():
    """
    Tworzenie nowego zadania (tylko dla administratora).
    GET: Wyświetla formularz tworzenia zadania
    POST: Tworzy nowe zadanie i automatycznie generuje kroki procesu
    """
    db = get_db()
    
    if request.method == 'POST':
        project_name = request.form['project_name']
        description = request.form.get('description', '')
        
        # Wstaw nowe zadanie do bazy (przypisane do obecnego administratora)
        cursor = db.execute('INSERT INTO tasks (project_name, description, admin_id) VALUES (?, ?, ?)',
                          (project_name, description, session['user_id']))
        # Pobierz ID nowo utworzonego zadania
        task_id = cursor.lastrowid
        
        # Automatycznie utwórz kroki procesu dla nowego zadania
        # Każdy krok ma przypisaną rolę (lub role oddzielone przecinkiem), która może go wykonać
        # Rozszerzona lista kroków zgodnie z wymaganiami działu KiT
        steps = [
            ('konstruktor', 'Przygotowanie rysunku ilustracji', 1),
            ('konstruktor,technolog', 'wykonanie ilustracji', 2),
            ('konstruktor', 'Przygotowanie rysunku do kroju (DXF/DWG)', 3),
            ('technolog', 'Opracowanie BOM (Arkusz: Elementy)', 4),
            ('technolog', 'Lista procesów z czasami', 5),
            ('technolog', 'przygotowanie wyceny', 6),
            ('technolog', 'potwierdzenie w ZS i Microsoft SharePoint', 7),
            ('wdrozeniowiec', 'wykonanie modelu', 8),
            ('wdrozeniowiec', 'Przygotowanie instrukcji krok po kroku', 9)
        ]
        
        # Wstaw wszystkie kroki do bazy danych
        for role, desc, order in steps:
            db.execute('INSERT INTO process_steps (task_id, role_required, description, step_order) VALUES (?, ?, ?, ?)',
                     (task_id, role, desc, order))
        
        # Zatwierdź zmiany w bazie
        db.commit()
        flash('Zadanie utworzone pomyślnie')
        return redirect(url_for('index'))
    
    # Wyświetl formularz (metoda GET)
    return render_template('new_task.html')

@app.route('/uploads/<filename>')
@login_required
def serve_file(filename):
    """
    Serwowanie plików z katalogu uploads.
    Sprawdza czy plik istnieje i wysyła go do przeglądarki.
    Wymaga zalogowania (dekorator @login_required).
    """
    # Połącz nazwę pliku z katalogiem uploads
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        # Wyślij plik do przeglądarki (możliwość otwarcia np. PDF w przeglądarce)
        return send_file(filepath)
    flash('Plik nie istnieje')
    return redirect(url_for('index'))


@app.route('/task/<int:task_id>/upload', methods=['POST'])
@login_required
def upload_file(task_id):
    """
    Wgrywanie plików dla konkretnego zadania.
    Zapisuje plik w katalogu uploads i dodaje rekord do bazy danych.
    Nazwa pliku zawiera ID zadania i timestamp, aby uniknąć kolizji nazw.
    """
    # Sprawdź czy w żądaniu jest plik
    if 'file' not in request.files:
        flash('Brak pliku')
        return redirect(url_for('view_task', task_id=task_id))
    
    file = request.files['file']
    # Sprawdź czy użytkownik wybrał plik
    if file.filename == '':
        flash('Nie wybrano pliku')
        return redirect(url_for('view_task', task_id=task_id))
    
    db = get_db()
    # Pobierz ID kroku (opcjonalne - plik może być ogólny dla zadania)
    step_id = request.form.get('step_id') or None
    
    # Wygeneruj unikalną nazwę pliku (zapobiega nadpisaniu plików o tej samej nazwie)
    filename = f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Zapisz plik na dysku
    file.save(filepath)
    
    # Dodaj informacje o pliku do bazy danych
    db.execute('INSERT INTO files (task_id, step_id, filename, file_path, file_type, uploaded_by) VALUES (?, ?, ?, ?, ?, ?)',
              (task_id, step_id, filename, filepath, file.content_type, session['user_id']))
    db.commit()
    
    flash('Plik wysłany')
    return redirect(url_for('view_task', task_id=task_id))


@app.route('/task/<int:task_id>')
@login_required
def view_task(task_id):
    """
    Wyświetlanie szczegółów zadania wraz z krokami procesu i plikami.
    Pobiera dane zadania, przypisane kroki oraz listę plików.
    """
    db = get_db()
    # Pobierz dane zadania
    task = db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    
    # Sprawdź czy zadanie istnieje
    if not task:
        flash('Zadanie nie istnieje')
        return redirect(url_for('index'))
    
    # Pobierz wszystkie kroki procesu dla tego zadania (posortowane według kolejności)
    steps = db.execute('SELECT * FROM process_steps WHERE task_id = ? ORDER BY step_order', (task_id,)).fetchall()
    
    # Pobierz wszystkie pliki przypisane do zadania wraz z nazwą użytkownika, który je wgrał
    files = db.execute('SELECT f.*, u.username FROM files f LEFT JOIN users u ON f.uploaded_by = u.id WHERE f.task_id = ?', (task_id,)).fetchall()
    
    return render_template('view_task.html', task=task, steps=steps, files=files)


@app.route('/task/<int:task_id>/step/<int:step_id>/complete', methods=['POST'])
@login_required
def complete_step(task_id, step_id):
    """
    Kończenie kroku procesu przez użytkownika.
    Sprawdza czy zalogowany użytkownik ma odpowiednią rolę do wykonania kroku.
    Obsługuje wiele ról w jednym kroku (oddzielone przecinkiem, np. 'konstruktor,technolog').
    Po zakończeniu wszystkich kroków, zadanie otrzymuje status 'zakończone'.
    """
    db = get_db()
    user_role = session.get('role')
    
    # Pobierz dane kroku
    step = db.execute('SELECT * FROM process_steps WHERE id = ? AND task_id = ?', (step_id, task_id)).fetchone()
    
    # Sprawdź czy rola użytkownika znajduje się w liście dozwolonych ról dla tego kroku
    # Role są przechowywane jako string oddzielony przecinkami (np. 'konstruktor,technolog')
    allowed_roles = [r.strip() for r in step['role_required'].split(',')]
    if user_role not in allowed_roles:
        flash('To zadanie nie jest przypisane do Twojej roli')
        return redirect(url_for('view_task', task_id=task_id))
    
    # Sprawdź czy krok nie został już ukończony
    if step['status'] == 'zakończone':
        flash('Ten krok został już zakończony')
        return redirect(url_for('view_task', task_id=task_id))
    
    # Pobierz czas wykonania wpisany przez użytkownika
    time_actual = request.form.get('time_actual')
    
    # Zaktualizuj krok jako zakończony
    db.execute('UPDATE process_steps SET status = ?, completed_by = ?, completed_at = ?, time_actual = ? WHERE id = ?',
             ('zakończone', session['user_id'], datetime.now(), time_actual, step_id))
    
    # Sprawdź czy wszystkie kroki w zadaniu zostały ukończone
    all_steps = db.execute('SELECT COUNT(*) as total, SUM(CASE WHEN status = "zakończone" THEN 1 ELSE 0 END) as completed FROM process_steps WHERE task_id = ?', (task_id,)).fetchone()
    
    # Jeśli wszystkie kroki ukończone - zmień status zadania na 'zakończone'
    if all_steps['total'] == all_steps['completed']:
        db.execute('UPDATE tasks SET status = ? WHERE id = ?', ('zakończone', task_id))
    
    # Zatwierdź zmiany w bazie
    db.commit()
    flash('Krok zakończony')
    return redirect(url_for('view_task', task_id=task_id))


if __name__ == '__main__':
    """
    Główny punkt wejścia aplikacji.
    Inicjalizuje bazę danych i uruchamia serwer Flask.
    - host='0.0.0.0' - serwer dostępny z innych komputerów w sieci LAN
    - port=5000 - port na którym działa aplikacja
    - debug=True - tryb debugowania (auto-reładowanie przy zmianach kodu)
    """
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
