from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.models.skill import Skill

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            if user.is_active:
                login_user(user, remember=remember)
                next_page = request.args.get('next')
                flash('Zalogowano pomyślnie!', 'success')
                return redirect(next_page or url_for('dashboard.index'))
            else:
                flash('Konto zostało dezaktywowane.', 'error')
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        # Role is always 'user' for registration, admins must be created by existing admins
        role = 'user'
        skill_ids = request.form.getlist('skills')

        # Validation
        if User.query.filter_by(username=username).first():
            flash('Nazwa użytkownika już istnieje.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email już istnieje.', 'error')
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash('Hasła nie są takie same.', 'error')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Hasło musi mieć co najmniej 6 znaków.', 'error')
            return redirect(url_for('auth.register'))

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        # Add skills
        if skill_ids:
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            user.skills.extend(skills)

        db.session.add(user)
        db.session.commit()

        flash('Konto zostało utworzone! Możesz się teraz zalogować.', 'success')
        return redirect(url_for('auth.login'))

    # Get available skills for registration
    skills = Skill.query.all()
    return render_template('auth/register.html', skills=skills)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Wylogowano pomyślnie.', 'info')
    return redirect(url_for('auth.login'))