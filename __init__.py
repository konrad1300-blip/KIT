from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user, UserMixin
import os
from sqlalchemy.orm import joinedload

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.options(joinedload(User.roles)).get(int(user_id))

def create_app(config_object='config.config.DevelopmentConfig'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config_object)

    from werkzeug.middleware.proxy_fix import ProxyFix

    class PrefixMiddleware:
        """Middleware usuwający prefiks subkatalogu (np. /app7) z PATH_INFO."""
        def __init__(self, app, prefix=None):
            self.app = app
            self.prefix = prefix

        def __call__(self, environ, start_response):
            # Pobierz prefiks z nagłówka Apache lub z zadanego prefixu
            prefix = self.prefix or environ.get('HTTP_X_FORWARDED_PREFIX', '')
            if prefix and environ['PATH_INFO'].startswith(prefix):
                environ['PATH_INFO'] = environ['PATH_INFO'][len(prefix):]
                environ['SCRIPT_NAME'] = prefix
            return self.app(environ, start_response)

    # Popraw nagłówki proxy (jeśli Apache przekazuje X-Forwarded-*)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    # Dodaj middleware usuwający prefiks /app7 (lub ogólnie z nagłówka X-Forwarded-Prefix)
    app.wsgi_app = PrefixMiddleware(app.wsgi_app)

    # Import models to ensure they are registered with SQLAlchemy metadata before initializing extensions
    from app import models  # noqa: F401

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db, directory='database/migrations')
    login_manager.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.steps import steps_bp
    from app.routes.users import users_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.reports import reports_bp, direct_bp
    from app.routes.step_templates import step_templates_bp
    from app.routes.project_templates import project_templates_bp
    from app.routes.import_routes import import_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(steps_bp, url_prefix='/steps')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(direct_bp)
    app.register_blueprint(step_templates_bp, url_prefix='/step-templates')
    app.register_blueprint(project_templates_bp, url_prefix='/project-templates')
    app.register_blueprint(import_bp, url_prefix='/import')

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Context processor for global template variables
    @app.context_processor
    def inject_globals():
        from app.models import Notification
        unread_notifications = []
        if current_user.is_authenticated:
            unread_notifications = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).order_by(Notification.created_at.desc()).limit(5).all()
        return dict(
            unread_notifications=unread_notifications,
            unread_count=len(unread_notifications)
        )

    return app
