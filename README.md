# KIT Application

Aplikacja do zarządzania projektami i zadaniami (KIT - Kolejka Inżynierów i Technologów).

## Funkcjonalności

### Podstawowe
- **Uwierzytelnianie**: Logowanie jako użytkownik lub administrator
- **Projekty**: Tworzenie, edycja, przeglądanie projektów
- **Zadania (kroki)**: Dodawanie kroków do projektów z przypisaniem do użytkowników
- **Filtrowanie**: Wyświetlanie zadań według statusu, daty, priorytetu, projektu
- **Priorytety**: Normalny, Wysoki, Pilny (do końca dnia), Bardzo pilny (natychmiast)
- **Statusy**: Do zrobienia, W trakcie, Zakończone
- **Matryca kompetencji**: Przypisywanie umiejętności do użytkowników

### Zaawansowane (planowane)
- Raporty PDF/Excel
- Powiadomienia email i in-app
- Archiwum zadań
- Wykresy obciążenia zespołu
- Komentarze przy zadaniach
- Zarządzanie plikami z wersjonowaniem
- Kalendarz i widok Gantta
- Automatyczne przypisywanie wykonawców
- Import/export danych
- Szablony zadań
- Workflow z zatwierdzaniem
- Zadania cykliczne
- Responsywny UI

## Struktura projektu

```
kit3/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── step.py
│   │   ├── skill.py
│   │   ├── notification.py
│   │   ├── log.py
│   │   ├── comment.py
│   │   └── file.py
│   ├── routes/              # Blueprints
│   │   ├── auth.py          # Authentication
│   │   ├── projects.py      # Projects CRUD
│   │   ├── steps.py         # Steps/Tasks CRUD
│   │   ├── users.py         # User management (admin)
│   │   ├── dashboard.py     # Main dashboard
│   │   └── reports.py       # Reports
│   ├── services/            # Business logic services
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── projects/
│   │   ├── steps/
│   │   └── users/
│   ├── static/              # CSS, JS, images
│   │   ├── css/
│   │   └── js/
│   └── config.py            # Configuration
├── config/                  # Environment configs
├── database/
│   └── migrations/          # Database migrations (Flask-Migrate)
├── init_db.py               # Database initialization script
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore
└── README.md
```

## Instalacja i konfiguracja

### 1. Wymagania
- Python 3.9+
- PostgreSQL 12+
- pip

### 2. Instalacja zależności
```bash
pip install -r requirements.txt
```

### 3. Konfiguracja bazy danych

#### Opcja A: Użycie PostgreSQL
1. Zainstaluj PostgreSQL
2. Utwórz bazę danych:
```sql
CREATE DATABASE kit3_db;
CREATE USER kit_user WITH PASSWORD 'twoje_haslo';
GRANT ALL PRIVILEGES ON DATABASE kit3_db TO kit_user;
```

3. Skonfiguruj zmienne środowiskowe w pliku `.env`:
```env
SECRET_KEY=twoj-tajny-klucz
DATABASE_URL=postgresql://kit_user:twoje_haslo@localhost/kit3_db
FLASK_ENV=production
```

#### Opcja B: Użycie SQLite (tylko do testów)
Dla szybkiego startu można użyć SQLite, ale aplikacja jest zaprojektowana pod PostgreSQL.
Zmodyfikuj `config/config.py` lub ustaw:
```env
DATABASE_URL=sqlite:///kit3.db
```

### 4. Inicjalizacja bazy danych
```bash
python init_db.py
```

To stworzy:
- Wszystkie tabele
- Domyślne umiejętności
- Administratora (login: `admin`, hasło: `admin123`)
- Przykładowego użytkownika (login: `technolog`, hasło: `technolog123`)

**WAŻNE: Zmień hasła w produkcji!**

### 5. Uruchomienie aplikacji

#### Tryb deweloperski:
```bash
python run.py
```

Lub z użyciem Flask:
```bash
export FLASK_APP=run.py
export FLASK_ENV=development
flask run
```

Aplikacja będzie dostępna pod adresem: http://localhost:5000

## Użycie

### Logowanie
- **Admin**: `admin` / `admin123`
- **Użytkownik**: `technolog` / `technolog123`

### Podstawowe przepływy pracy

#### Administrator może:
1. **Zarządzać użytkownikami**: dodawać, edytować, deaktywować
2. **Przypisywać umiejętności** do użytkowników
3. **Tworzyć projekty** i przypisywać do nich zadania
4. **Edytować wszystkie zadania**
5. **Generować raporty** (kiedyś dostępne)

#### Użytkownik może:
1. **Przeglądać swoje zadania** (przypisane do niego)
2. **Filtrować** według statusu (Do zrobienia, W trakcie, Zakończone)
3. **Filtrować** według daty terminów
4. **Zmieniać status** zadań (▶ → ✓ → ○)
5. **Dodawać komentarze** do zadań
6. **Przeglądać szczegóły** projektów

### Priorytety zadań
1. **Bardzo pilny (natychmiast)** - czerwony, najwyższy priorytet sortowania
2. **Pilny (do końca dnia)** - pomarańczowy
3. **Wysoki** - żółty
4. **Normalny** - szary

### Typy kroków
Każdy typ ma powiązane wymagane umiejętności:

| Typ kroku | Wymagane umiejętności |
|-----------|---------------------|
| Wykonanie modelu - wdrożeniowiec | Modelowanie 3D, CAD, Wdrożeniowiec |
| Potwierdzenie w ZS i SharePoint - technolog | SharePoint, Dokumentacja techniczna |
| Wykonanie ilustracji - technolog | Ilustracje techniczne, CAD |
| Wykonanie ilustracji - konstruktor | Ilustracje konstrukcyjne, Projektowanie |
| Przygotowanie wyceny - technolog | Przygotowanie wyceny, Analiza BOM |

## API Endpoints

### Publiczne (wymaga logowania)
- `GET /` - Dashboard
- `GET /projects` - Lista projektów
- `GET /projects/<id>` - Szczegóły projektu
- `GET /steps` - Lista zadań z filtrami
- `GET /steps/<id>` - Szczegóły zadania
- `GET /users/<id>` - Profil użytkownika

### Administrator
- `GET /users` - Lista użytkowników
- `POST /users/create` - Tworzenie użytkownika
- `POST /users/<id>/toggle-active` - Aktywacja/deaktywacja
- `GET /users/skills` - Zarządzanie umiejętnościami

### AJAX
- `POST /steps/<id>/status/<status>` - Szybka zmiana statusu
- `POST /steps/<id>/comment` - Dodaj komentarz
- `GET /api/stats` - Statystyki dashboardu (JSON)

## Administracja

### Zmiana hasła
1. Zaloguj się jako admin
2. Przejdź do profilu (lub użyj `/users/<id>/edit`)
3. Wprowadź nowe hasło i zapisz

### Resetowanie hasła użytkownika
Jako admin przejdź do edycji użytkownika i ustaw nowe hasło.

### Backup bazy danych
```bash
pg_dump -U postgres kit3_db > backup_$(date +%Y%m%d).sql
```

### Restore bazy danych
```bash
psql -U postgres kit3_db < backup_20240101.sql
```

## Rozwiązywanie problemów

### Błąd "password hash not supported"
Zaktualizuj `requirements.txt`:
```
werkzeug==3.0.1
```

### Błąd połączenia z PostgreSQL
Sprawdź:
1. Czy PostgreSQL jest uruchomiony: `sudo systemctl status postgresql`
2. Czy baza danych istnieje: `psql -U postgres -l`
3. Czy użytkownik ma uprawnienia

### Migracje bazy danych
Jeśli zmieniasz modele, użyj Flask-Migrate:
```bash
flask db init
flask db migrate -m "opis zmian"
flask db upgrade
```

## Bezpieczeństwo

### W produkcji:
1. **Zmień domyślne hasła**!
2. Użyj silnego `SECRET_KEY`
3. Włącz HTTPS
4. Ogranicz dostęp do portu 5000 (firewall)
5. Regularnie aktualizuj zależności
6. Skonfiguruj backup bazy danych
7. Włącz logowanie (audit trail)
8. Rozważ użycie Flask-Talisman dla nagłówków bezpieczeństwa

## Rozwój

### Dodawanie nowego typu kroku
1. Dodaj wartość do `step_type` w template `steps/form.html`
2. Zaktualizuj mapping umiejętności w `models/step.py` (metoda `can_user_execute`)
3. Możesz dodać ikonę lub specjalną logikę

### Rozszerzanie umiejętności
Umiejętności są w tabeli `skills`. Możesz dodawać nowe przez admin panel lub bezpośrednio w bazie.

## Licencja

Internal use only - KIT Organization

## Kontakt

W przypadku pytań technicznych skontaktuj się z zespołem developerskim.