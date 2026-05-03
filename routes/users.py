from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models.user import User
from app.models.skill import Skill
from app.models.step import Step
from app.models.role import Role
from app.models.log import Log
from datetime import datetime
import io

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
@login_required
def list_users():
    """List all users (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może przeglądać listę użytkowników.', 'error')
        return redirect(url_for('dashboard.index'))

    users = User.query.order_by(User.username).all()
    return render_template('users/list.html', users=users, skills=Skill.query.all())

@users_bp.route('/export')
@login_required
def export_users():
    """Eksportuj użytkowników do Excel (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może eksportować dane.', 'error')
        return redirect(url_for('users.list_users'))
    
    from app.services.import_export import export_users_to_excel
    try:
        output = export_users_to_excel()
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='uzytkownicy_kit.xlsx'
        )
    except Exception as e:
        flash(f'Błąd eksportu: {str(e)}', 'error')
        return redirect(url_for('users.list_users'))

@users_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_users():
    """Importuj użytkowników z Excela (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może importować dane.', 'error')
        return redirect(url_for('users.list_users'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nie wybrano pliku.', 'error')
            return redirect(url_for('users.import_users'))
        
        file = request.files['file']
        if file.filename == '':
            flash('Nie wybrano pliku.', 'error')
            return redirect(url_for('users.import_users'))
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Plik musi być w formacie Excel (.xlsx lub .xls).', 'error')
            return redirect(url_for('users.import_users'))
        
        try:
            from app.services.import_export import import_users_from_excel
            result = import_users_from_excel(file.stream, current_user.id)
            
            if result['success'] or result['imported'] > 0 or result['updated'] > 0:
                if result['imported'] > 0:
                    flash(f'Zaimportowano {result["imported"]} nowych użytkowników.', 'success')
                if result['updated'] > 0:
                    flash(f'Zaktualizowano {result["updated"]} istniejących użytkowników.', 'info')
                if result['errors']:
                    flash(f'Uwagi: {", ".join(result["errors"][:5])}', 'warning')
            else:
                flash('Nie zaimportowano żadnych danych.', 'warning')
                if result['errors']:
                    for err in result['errors'][:5]:
                        flash(err, 'warning')
        except Exception as e:
            flash(f'Błąd importu: {str(e)}', 'error')
        
        return redirect(url_for('users.list_users'))
    
    return render_template('users/import.html')

@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_user():
    """Create new user (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może dodawać użytkowników.', 'error')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role_ids = request.form.getlist('roles')
        skill_ids = request.form.getlist('skills')

        # Validation
        if User.query.filter_by(username=username).first():
            flash('Nazwa użytkownika już istnieje.', 'error')
            return redirect(url_for('users.create_user'))

        if User.query.filter_by(email=email).first():
            flash('Email już istnieje.', 'error')
            return redirect(url_for('users.create_user'))

        if password != confirm_password:
            flash('Hasła nie są takie same.', 'error')
            return redirect(url_for('users.create_user'))

        if len(password) < 6:
            flash('Hasło musi mieć co najmniej 6 znaków.', 'error')
            return redirect(url_for('users.create_user'))

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name
        )

        # Add roles
        if role_ids:
            from app.models.role import Role
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            user.roles.extend(roles)

        # Add skills
        if skill_ids:
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            user.skills.extend(skills)

        db.session.add(user)

        # Log action
        role_names = [role.name for role in user.roles]
        log = Log(
            user_id=current_user.id,
            action='create_user',
            resource_type='user',
            resource_id=user.id,
            details=f'Created user: {username} with roles: {", ".join(role_names)}'
        )
        db.session.add(log)
        db.session.commit()

        flash(f'Użytkownik {username} został utworzony!', 'success')
        return redirect(url_for('users.list_users'))

    skills = Skill.query.all()
    from app.models.role import Role
    roles = Role.query.all()
    return render_template('users/form.html', user=None, skills=skills, roles_list=roles)

@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit user (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może edytować użytkowników.', 'error')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=user.email).first()
        if existing_user and existing_user.id != user.id:
            flash('Email już istnieje.', 'error')
            return redirect(url_for('users.edit_user', user_id=user.id))
        
        # Only update password if provided
        password = request.form.get('password')
        if password and len(password) >= 6:
            user.password_hash = generate_password_hash(password)

        # Update roles
        role_ids = request.form.getlist('roles')
        from app.models.role import Role
        user.roles = []  # Clear existing
        if role_ids:
            roles = Role.query.filter(Role.id.in_(role_ids)).all()
            user.roles.extend(roles)

        # Update skills
        skill_ids = request.form.getlist('skills')
        user.skills = []  # Clear existing
        if skill_ids:
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            user.skills.extend(skills)

        # Log action
        role_names = [role.name for role in user.roles]
        log = Log(
            user_id=current_user.id,
            action='update_user',
            resource_type='user',
            resource_id=user.id,
            details=f'Updated user: {user.username}, roles: {", ".join(role_names)}'
        )
        db.session.add(log)
        db.session.commit()

        flash(f'Użytkownik {user.username} został zaktualizowany!', 'success')
        return redirect(url_for('users.list_users'))

    skills = Skill.query.all()
    from app.models.role import Role
    roles = Role.query.all()
    return render_template('users/form.html', user=user, skills=skills, roles_list=roles)

@users_bp.route('/<int:user_id>/toggle-active', methods=['POST'])
@login_required
def toggle_active(user_id):
    """Toggle user active status (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może zmieniać status użytkownika.', 'error')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active

    action = 'activate_user' if user.is_active else 'deactivate_user'
    log = Log(
        user_id=current_user.id,
        action=action,
        resource_type='user',
        resource_id=user.id,
        details=f'Changed active status for: {user.username}'
    )
    db.session.add(log)
    db.session.commit()

    status = 'aktywowany' if user.is_active else 'dezaktywowany'
    flash(f'Użytkownik {user.username} został {status}!', 'success')
    return redirect(url_for('users.list_users'))

@users_bp.route('/<int:user_id>')
@login_required
def view_user(user_id):
    """View user details"""
    if not current_user.has_role('admin') and current_user.id != user_id:
        flash('Nie masz uprawnień do przeglądania tego profilu.', 'error')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)
    assigned_steps = Step.query.filter_by(assigned_to=user_id).order_by(Step.due_date).all()
    created_steps = Step.query.filter_by(created_by=user_id).order_by(Step.created_at.desc()).limit(10).all()

    return render_template('users/view.html',
                         user=user,
                         assigned_steps=assigned_steps,
                         created_steps=created_steps)

@users_bp.route('/skills')
@login_required
def list_skills():
    """List all skills (admin only for management)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może zarządzać umiejętnościami.', 'error')
        return redirect(url_for('dashboard.index'))

    skills = Skill.query.order_by(Skill.category, Skill.name).all()
    return render_template('users/skills.html', skills=skills)

@users_bp.route('/skills/create', methods=['GET', 'POST'])
@login_required
def create_skill():
    """Create new skill (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może dodawać umiejętności.', 'error')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')

        if Skill.query.filter_by(name=name).first():
            flash('Umiejętność o tej nazwie już istnieje.', 'error')
            return redirect(url_for('users.create_skill'))

        skill = Skill(name=name, description=description, category=category)
        db.session.add(skill)

        log = Log(
            user_id=current_user.id,
            action='create_skill',
            resource_type='skill',
            details=f'Created skill: {name}'
        )
        db.session.add(log)
        db.session.commit()

        flash('Umiejętność została dodana!', 'success')
        return redirect(url_for('users.list_skills'))

    return render_template('users/skill_form.html', skill=None)

@users_bp.route('/skills/<int:skill_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_skill(skill_id):
    """Edit skill (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może edytować umiejętności.', 'error')
        return redirect(url_for('dashboard.index'))

    skill = Skill.query.get_or_404(skill_id)

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')

        if not name:
            flash('Nazwa umiejętności jest wymagana.', 'error')
            return redirect(url_for('users.edit_skill', skill_id=skill.id))

        # Check if another skill with this name exists (excluding current skill)
        existing_skill = Skill.query.filter(Skill.name == name, Skill.id != skill.id).first()
        if existing_skill:
            flash('Umiejętność o tej nazwie już istnieje.', 'error')
            return redirect(url_for('users.edit_skill', skill_id=skill.id))

        skill.name = name
        skill.description = description
        skill.category = category

        log = Log(
            user_id=current_user.id,
            action='update_skill',
            resource_type='skill',
            resource_id=skill.id,
            details=f'Updated skill: {name}'
        )
        db.session.add(log)
        db.session.commit()

        flash('Umiejętność została zaktualizowana!', 'success')
        return redirect(url_for('users.list_skills'))

    return render_template('users/skill_form.html', skill=skill)


@users_bp.route('/skills/<int:skill_id>/delete', methods=['POST'])
@login_required
def delete_skill(skill_id):
    """Delete skill (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może usuwać umiejętności.', 'error')
        return redirect(url_for('dashboard.index'))

    skill = Skill.query.get_or_404(skill_id)
    skill_name = skill.name
    db.session.delete(skill)

    log = Log(
        user_id=current_user.id,
        action='delete_skill',
        resource_type='skill',
        details=f'Deleted skill: {skill_name}'
    )
    db.session.add(log)
    db.session.commit()

    flash('Umiejętność została usunięta!', 'success')
    return redirect(url_for('users.list_skills'))


@users_bp.route('/<int:user_id>/remove_skill/<int:skill_id>', methods=['POST'])
@login_required
def remove_skill(user_id, skill_id):
    """Remove skill from user (admin only)"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może zarządzać umiejętnościami użytkowników.', 'error')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)
    skill = Skill.query.get_or_404(skill_id)

    if skill in user.skills:
        user.skills.remove(skill)

        log = Log(
            user_id=current_user.id,
            action='remove_skill_from_user',
            resource_type='user',
            resource_id=user.id,
            details=f'Removed skill {skill.name} from user {user.username}'
        )
        db.session.add(log)
        db.session.commit()

        flash(f'Umiętność {skill.name} została usunięta od użytkownika {user.username}!', 'success')
    else:
        flash('Użytkownik nie posiada tej umiejętności.', 'warning')

    return redirect(url_for('users.edit_user', user_id=user.id))