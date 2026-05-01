# KILO Configuration for KIT Application

## Project Information
- **Name**: KIT Application (Kolejka Inżynierów i Technologów)
- **Type**: Flask web application with PostgreSQL
- **Purpose**: Project and task management system with skills matrix

## Commands

### Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database (first time setup)
python init_db.py

# Run development server
python run.py

# Or using Flask
export FLASK_APP=run.py
export FLASK_ENV=development
flask run
```

### Database Commands

```bash
# Initialize/seed database
python init_db.py

# Using Flask-Migrate (if migrations exist)
flask db init
flask db migrate -m "description"
flask db upgrade
flask db downgrade
```

### Testing Commands
(To be added when test suite is created)

```bash
# Run tests
pytest

# With coverage
pytest --cov=app
```

## Files and Directories

### Critical files to modify
- `app/models/` - Database models (User, Project, Step, Skill, etc.)
- `app/routes/` - Route handlers/controllers
- `app/templates/` - HTML templates
- `app/static/` - CSS and JavaScript files
- `config/config.py` - Application configuration
- `requirements.txt` - Python dependencies

### Configuration files
- `.env` - Environment variables (not in repo, use `.env.example`)
- `config/config.py` - Flask configuration object

### Database files
- `init_db.py` - Database initialization/seed script
- `database/migrations/` - migration files (auto-generated)

## Development Workflow

1. **Database changes**:
   - Modify models in `app/models/`
   - Run `flask db migrate` to create migration
   - Run `flask db upgrade` to apply

2. **Add new feature**:
   - Create new route blueprint in `app/routes/` if needed
   - Add templates in `app/templates/`
   - Update `app/__init__.py` to register new blueprints
   - Test thoroughly

3. **Styling changes**:
   - Edit `app/static/css/styles.css`
   - Test responsive design

4. **JavaScript changes**:
   - Edit `app/static/js/main.js`

## Ports and Services

- **Development**: http://localhost:5000
- **PostgreSQL**: localhost:5432
- **Database name**: kit3_db (development)

## User Credentials (Default)

After running `init_db.py`:
- **Admin**: admin / admin123
- **User**: technolog / technolog123

⚠️ **Change these in production!**

## Notes

- Application uses Flask blueprints for modularity
- Authentication via Flask-Login with session management
- PostgreSQL for production, SQLite possible for dev
- Audit logging on all significant actions
- Role-based access control (user/admin)
- Skills matrix for intelligent task assignment
- Notification system (in-app, email ready)
- Priority-based sorting with time-sensitive tiers
- Multi-status workflow (pending, in_progress, completed)

## Environment Variables

```env
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=postgresql://localhost/kit3_db
FLASK_ENV=development
FLASK_DEBUG=1
```

## Database Schema Overview

- **users** - User accounts with roles and authentication
- **projects** - Project definitions
- **steps** - Individual tasks linked to projects
- **skills** - Predefined skill list
- **user_skills** - Many-to-many user↔skill
- **notifications** - In-app notifications
- **logs** - Audit trail
- **comments** - Task discussions
- **files** - File attachments with versioning

## Known Limitations / Future Work

- Reports (PDF/Excel export) yet to be implemented
- Email notifications need SMTP config
- File upload not fully implemented
- Calendar/Gantt view pending
- Import/Export pending
- Recurring tasks pending
- Approval workflow pending
- Mobile responsive needs testing

## Testing Checklist

- [ ] User registration/login works
- [ ] Admin can create/edit users
- [ ] Projects CRUD works
- [ ] Steps CRUD works
- [ ] Filtering by status/date works
- [ ] Priority sorting works
- [ ] Skills matrix works
- [ ] Comments can be added
- [ ] Audit logs are created
- [ ] Notifications are generated
- [ ] Status color coding works
- [ ] Responsive design works

## Support

For issues or questions, refer to the project documentation or contact the development team.