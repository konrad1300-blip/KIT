# Szybki start - KIT Application

## 5-minutowy setup

### 1. Instalacja zależności
```bash
pip install -r requirements.txt
```

### 2. Przygotuj bazę PostgreSQL
```bash
# Zaloguj się do PostgreSQL
sudo -u postgres psql

# W psql:
CREATE DATABASE kit3_db;
CREATE USER kit_user WITH PASSWORD 'kit_pass';
GRANT ALL PRIVILEGES ON DATABASE kit3_db TO kit_user;
\q
```

### 3. Konfiguracja
```bash
cp .env.example .env
```

Edytuj `.env`:
```env
SECRET_KEY=zmien-this-w-produkcji-12345
DATABASE_URL=postgresql://kit_user:kit_pass@localhost/kit3_db
FLASK_ENV=development
FLASK_DEBUG=1
```

### 4. Inicjalizuj bazę danych
```bash
python init_db.py
```

### 5. Uruchom aplikację
```bash
python run.py
```

### 6. Otwórz w przeglądarce
```
http://localhost:5000
```

## Logowania

| Rola | Login | Hasło |
|------|-------|-------|
| Admin | admin | admin123 |
| Użytkownik | technolog | technolog123 |

**⚠️ Zmień hasła w tym .env i przez panel admina!**

## Co możesz zrobić

### Jako Admin:
- Zarządzaj użytkownikami (dodawaj, edytuj, dezaktywuj)
- Przypisuj umiejętności użytkownikom
- Twórz projekty i zadania
- Przeglądaj wszystkie zadania wszystkich użytkowników
- Generuj raporty (kiedyś)

### Jako Użytkownik:
- Przeglądaj swoje zadania
- Filtruj po statusie (do zrobienia / w trakcie / zakończone)
- Filtruj po dacie
- Zmieniaj status zadań (▶ W trakcie → ✓ Zakończ → ○ Do zrobienia)
- Dodawaj komentarze
- Śledź terminy

## Typy zadań i ich umiejętności

| Typ kroku | Wymagane umiejętności | Dla kogo |
|-----------|---------------------|----------|
| Wykonanie modelu - wdrożeniowiec | Modelowanie 3D, CAD | Wdrożeniowiec |
| Potwierdzenie w ZS i SharePoint | SharePoint, Dokumentacja | Technolog |
| Wykonanie ilustracji - technolog | Ilustracje techniczne, CAD | Technolog |
| Wykonanie ilustracji - konstruktor | Ilustracje konstrukcyjne | Konstruktor |
| Przygotowanie wyceny | Wycena, Analiza BOM | Technolog |

System **automatycznie sprawdza** czy użytkownik ma wymagane umiejętności przed przypisaniem zadania.

## Priorytety zadań (sortowanie od najwyższego):

1. **Bardzo pilny** (czerwony) - natychmiast
2. **Pilny** (pomarańczowy) - do końca dnia
3. **Wysoki** (żółty)
4. **Normalny** (szary)

## Struktura plików

```
kit3/
├── app/
│   ├── models/    # Tabele bazy danych
│   ├── routes/    # Kontrolery (API endpoints)
│   ├── templates/ # Strony HTML
│   └── static/    # CSS/JS
├── config/        # Konfiguracja
├── init_db.py     # Setup bazy
└── run.py         # Start aplikacji
```

## Najważniejsze endpointy

| Ścieżka | Opis |
|---------|------|
| `/` | Dashboard główny |
| `/projects` | Lista projektów |
| `/projects/<id>` | Szczegóły projektu + zadania |
| `/projects/create` | Nowy projekt |
| `/steps` | Lista wszystkich zadań z filtrami |
| `/steps/<id>` | Szczegóły zadania |
| `/users` | Lista użytkowników (admin) |
| `/users/skills` | Zarządzanie umiejętnościami (admin) |

## Filtrowanie zadań

W `/steps` możesz filtrować przez:
- **Status**: do zrobienia / w trakcie / zakończone
- **Priorytet**: normalny / wysoki / pilny / bardzo pilny
- **Projekt**: wybierz z listy
- **Przypisane do**: (admin) wybierz użytkownika
- **Data od/do**: zakres terminów
- **Opóźnione**: pokazuje tylko te po terminie
- **Szukaj**: po nazwie zadania

Sortuj klikając nagłówki kolumn: Termin, Priorytet, Data utworzenia.

## Problem? Sprawdź:

1. **Błąd połączenia z bazą?** Upewnij się PostgreSQL działa:
   ```bash
   sudo systemctl status postgresql
   ```

2. **Moduły nie znalezione?** Zainstaluj:
   ```bash
   pip install -r requirements.txt
   ```

3. **Tabele nie istnieją?** Uruchom ponownie:
   ```bash
   python init_db.py
   ```

4. **Hash password error?** Upewnij się wersja werkzeug:
   ```
   werkzeug==3.0.1
   ```

## Co dalej?

Faza 1 jest **gotowa do użycia**. Możesz:
1. Testować wszystkie funkcje
2. Dodawać nowych użytkowników
3. Tworzyć projekty i zadania
4. Przeprowadzić demo

Faza 2 (raporty, wykresy, pliki, kalendarz) implementuj przyrostowo bez przerywania działania.

## Dokumentacja

- `README.md` - Pełna dokumentacja
- `AGENTS.md` - Dla narzędzi developerskich
- `IMPLEMENTATION_SUMMARY.md` - Szczegóły implementacji
- `Plan zmian.txt` - Oryginalne wymagania

Powodzenia! 🚀