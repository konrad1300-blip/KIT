from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_required, current_user
from app import db
from app.models.project import Project
from app.models.step import Step
from app.models.project_template import ProjectTemplate
from app.models.step_template import StepTemplate
from app.models.role import Role
from app.models.log import Log
from app.models.notification import Notification
from datetime import datetime, timedelta
import io

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/')
@login_required
def list_projects():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    query = Project.query
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
    search = request.args.get('search')
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%'))
    projects = query.order_by(Project.priority.desc(), Project.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return render_template('projects/list.html', projects=projects)

@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        priority = request.form.get('priority', 2, type=int)
        due_date_str = request.form.get('due_date')
        project_template_id = request.form.get('project_template_id', type=int)
        if not name:
            flash('Nazwa projektu jest wymagana.', 'error')
            return redirect(url_for('projects.create_project'))
        project = Project(
            name=name, description=description, priority=priority,
            created_by=current_user.id, project_template_id=project_template_id)
        if due_date_str:
            project.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        db.session.add(project)
        db.session.flush()
        if project_template_id:
            project_template = ProjectTemplate.query.get(project_template_id)
            if project_template:
                for step_template in project_template.step_templates:
                    step = Step(
                        name=step_template.name, description=step_template.description,
                        step_type=step_template.step_type, priority=step_template.priority,
                        estimated_time=step_template.estimated_time, project_id=project.id,
                        created_by=current_user.id, template_id=step_template.id)
                    db.session.add(step)
                    db.session.flush()
        log = Log(
            user_id=current_user.id, action='create_project',
            resource_type='project', resource_id=project.id,
            details=f'Created project: {name}')
        db.session.add(log)
        db.session.commit()
        flash('Projekt został utworzony!', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    project_templates = None
    if current_user.has_role('admin'):
        project_templates = ProjectTemplate.query.filter_by(is_active=True).order_by(ProjectTemplate.name).all()
    return render_template('projects/form.html', project=None, project_templates=project_templates)

@projects_bp.route('/<int:project_id>')
@login_required
def view_project(project_id):
    project = Project.query.get_or_404(project_id)
    steps = project.steps.order_by(Step.priority.desc(), Step.created_at).all()
    steps_by_status = {
        'pending': [s for s in steps if s.status == 'pending'],
        'in_progress': [s for s in steps if s.status == 'in_progress'],
        'completed': [s for s in steps if s.status == 'completed']
    }
    return render_template('projects/view.html',
        project=project, steps_by_status=steps_by_status,
        steps=steps,  # Pass ordered steps list
        total_steps=len(steps), completed_steps=len(steps_by_status['completed']))

@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    if not current_user.has_role('admin'):
        flash('Tylko administrator może edytować projekty.', 'error')
        return redirect(url_for('dashboard.index'))
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        project.priority = request.form.get('priority', 2, type=int)
        project.status = request.form.get('status', 'active')
        due_date_str = request.form.get('due_date')
        if due_date_str:
            project.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        else:
            project.due_date = None
        db.session.commit()
        log = Log(
            user_id=current_user.id, action='update_project',
            resource_type='project', resource_id=project.id,
            details=f'Updated project: {project.name}')
        db.session.add(log)
        db.session.commit()
        flash('Projekt został zaktualizowany!', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    return render_template('projects/form.html', project=project)

@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    if not current_user.has_role('admin'):
        flash('Tylko administrator może usuwać projekty.', 'error')
        return redirect(url_for('projects.list_projects'))
    project = Project.query.get_or_404(project_id)
    log = Log(
        user_id=current_user.id, action='delete_project',
        resource_type='project', details=f'Deleted project: {project.name}')
    db.session.add(log)
    db.session.delete(project)
    db.session.commit()
    flash('Projekt został usunięty!', 'success')
    return redirect(url_for('projects.list_projects'))

@projects_bp.route('/<int:project_id>/archive', methods=['POST'])
@login_required
def archive_project(project_id):
    if not current_user.has_role('admin'):
        flash('Tylko administrator może archiwizować projekty.', 'error')
        return redirect(url_for('projects.list_projects'))
    project = Project.query.get_or_404(project_id)
    project.status = 'archived'
    log = Log(
        user_id=current_user.id, action='archive_project',
        resource_type='project', resource_id=project.id,
        details=f'Archived project: {project.name}')
    db.session.add(log)
    db.session.commit()
    flash('Projekt został zarchiwizowany!', 'success')
    return redirect(url_for('projects.list_projects'))

@projects_bp.route('/<int:project_id>/steps/create', methods=['GET', 'POST'])
@login_required
def create_step(project_id):
    project = Project.query.get_or_404(project_id)
    
    def _update_project_status(project_id):
        project = Project.query.get(project_id)
        if not project:
            return
        # Do not update status if project is archived
        if project.status == 'archived':
            return
        steps = Step.query.filter_by(project_id=project_id).all()
        if not steps:
            return
        all_completed = all(step.status == 'completed' for step in steps)
        any_in_progress = any(step.status == 'in_progress' for step in steps)
        if all_completed:
            project.status = 'completed'
        elif any_in_progress:
            project.status = 'active'
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        step_type = request.form.get('step_type')
        assigned_to = request.form.get('assigned_to', type=int)
        estimated_time = request.form.get('estimated_time', type=int)
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'normal')
        notes = request.form.get('notes')
        required_role_ids = request.form.getlist('required_roles')
        
        if not name:
            flash('Nazwa kroku jest wymagana.', 'error')
            return redirect(url_for('projects.create_step', project_id=project.id))
        
        step = Step(
            name=name, description=description, step_type=step_type,
            assigned_to=assigned_to, created_by=current_user.id,
            estimated_time=estimated_time, priority=priority,
            project_id=project.id, notes=notes)
        
        if due_date_str:
            step.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        
        # Set required roles
        from app.models.role import Role
        if required_role_ids:
            roles = Role.query.filter(Role.id.in_(required_role_ids)).all()
            step.required_roles.extend(roles)
        
        # Validate: if there are required roles, assigned user must have at least one
        if step.required_roles and assigned_to:
            assignee = User.query.get(assigned_to)
            if assignee and not assignee.has_any_role([role.name for role in step.required_roles]):
                role_names = [role.display_name for role in step.required_roles]
                flash(f'Użytkownik {assignee.full_name} nie posiada wymaganych ról: {", ".join(role_names)}.', 'error')
                return redirect(url_for('projects.create_step', project_id=project.id))
        
        db.session.add(step)
        db.session.flush()
        
        if assigned_to:
            notification = Notification(
                user_id=assigned_to, title='Nowe zadanie przypisane',
                message=f'Zostałeś przypisany do kroku: {name}',
                notification_type='assignment',
                link=url_for('steps.edit_step', step_id=step.id))
            db.session.add(notification)
        
        log = Log(
            user_id=current_user.id, action='create_step',
            resource_type='step', resource_id=step.id,
            details=f'Created step: {name} for project {project.name}')
        db.session.add(log)
        _update_project_status(project.id)
        db.session.commit()
        
        flash('Krok został utworzony!', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    from app.models import User, Skill, Role
    users = User.query.all()
    roles = Role.query.all()
    return render_template('projects/create_step.html',
        project=project, users=users, roles=roles)

@projects_bp.route('/export')
@login_required
def export_projects():
    from app.services.import_export import export_projects_to_excel
    try:
        output = export_projects_to_excel(Project.query)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True, download_name='projekty_kit.xlsx')
    except Exception as e:
        flash(f'Błąd eksportu: {str(e)}', 'error')
        return redirect(url_for('projects.list_projects'))

@projects_bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_projects():
    if not current_user.has_role('admin'):
        flash('Tylko administrator może importować dane.', 'error')
        return redirect(url_for('projects.list_projects'))
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nie wybrano pliku.', 'error')
            return redirect(url_for('projects.import_projects'))
        file = request.files['file']
        if file.filename == '':
            flash('Nie wybrano pliku.', 'error')
            return redirect(url_for('projects.import_projects'))
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Plik musi być w formacie Excel (.xlsx lub .xls).', 'error')
            return redirect(url_for('projects.import_projects'))
        try:
            from app.services.import_export import import_projects_from_excel
            result = import_projects_from_excel(file.stream, current_user.id)
            if result['success'] or result['imported'] > 0 or result['updated'] > 0:
                if result['imported'] > 0:
                    flash(f'Zaimportowano {result["imported"]} nowych projektów.', 'success')
                if result['updated'] > 0:
                    flash(f'Zaktualizowano {result["updated"]} istniejących projektów.', 'info')
                if result['errors']:
                    flash(f'Uwagi: {", ".join(result["errors"][:5])}', 'warning')
            else:
                flash('Nie zaimportowano żadnych danych.', 'warning')
                if result['errors']:
                    for err in result['errors'][:5]:
                        flash(err, 'warning')
        except Exception as e:
            flash(f'Błąd importu: {str(e)}', 'error')
        return redirect(url_for('projects.list_projects'))
    return render_template('projects/import.html')

@projects_bp.route('/<int:project_id>/pdf')
@login_required
def project_pdf(project_id):
    import weasyprint
    project = Project.query.get_or_404(project_id)
    steps = project.steps.order_by(Step.priority.desc(), Step.created_at).all()
    total = len(steps)
    completed = len([s for s in steps if s.status == 'completed'])
    in_progress = len([s for s in steps if s.status == 'in_progress'])
    pending = len([s for s in steps if s.status == 'pending'])
    html = render_template('reports/project_pdf.html',
        project=project, steps=steps, total=total, completed=completed,
        in_progress=in_progress, pending=pending,
        completion_pct=project.completion_percentage)
    pdf = weasyprint.HTML(string=html, base_url='/').write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=projekt_{project.name[:50]}.pdf'
    return response

@projects_bp.route('/user/<int:user_id>/weekly-pdf')
@login_required
def user_weekly_pdf(user_id):
    import weasyprint
    user = User.query.get_or_404(user_id)
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_ago = datetime.utcnow() - timedelta(days=7)
    completed_steps = Step.query.filter(
        Step.assigned_to == user_id, Step.status == 'completed',
        Step.completed_at >= week_ago).order_by(Step.completed_at.desc()).all()
    total_time = sum(s.actual_time or s.estimated_time or 0 for s in completed_steps)
    html = render_template('reports/user_weekly_pdf.html',
        user=user, completed_steps=completed_steps, total_time=total_time,
        week_ago=week_ago, report_date=datetime.utcnow())
    pdf = weasyprint.HTML(string=html, base_url='/').write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=raport_{user.username}_tydzien.pdf'
    return response

@projects_bp.route('/user/<int:user_id>/monthly-pdf')
@login_required
def user_monthly_pdf(user_id):
    import weasyprint
    user = User.query.get_or_404(user_id)
    month_ago = datetime.utcnow() - timedelta(days=30)
    completed_steps = Step.query.filter(
        Step.assigned_to == user_id, Step.status == 'completed',
        Step.completed_at >= month_ago).order_by(Step.completed_at.desc()).all()
    total_time = sum(s.actual_time or s.estimated_time or 0 for s in completed_steps)
    html = render_template('reports/user_monthly_pdf.html',
        user=user, completed_steps=completed_steps, total_time=total_time,
        month_ago=month_ago, report_date=datetime.utcnow())
    pdf = weasyprint.HTML(string=html, base_url='/').write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=raport_{user.username}_miesiac.pdf'
    return response

@projects_bp.route('/team/pdf')
@login_required
def team_pdf():
    import weasyprint
    if not current_user.has_role('admin'):
        flash('Tylko administrator może generować raporty zespołowe.', 'error')
        return redirect(url_for('dashboard.index'))
    # Get users who are not admins (based on roles - exclude users with admin role)
    # Using subquery to find users without admin role
    from app.models.role import Role
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_role:
        users = User.query.filter(~User.roles.any(id=admin_role.id)).all()
    else:
        users = User.query.all()
    team_data = []
    total_open_steps = total_overdue = 0
    for user in users:
        open_steps = Step.query.filter(Step.assigned_to == user.id, Step.status != 'completed').all()
        completed_count = Step.query.filter(Step.assigned_to == user.id, Step.status == 'completed').count()
        overdue_steps = Step.query.filter(Step.assigned_to == user.id, Step.due_date < datetime.utcnow(), Step.status != 'completed').all()
        total_time = sum(s.estimated_time or 0 for s in open_steps)
        team_data.append({'user': user, 'open_steps': open_steps, 'open_count': len(open_steps),
            'completed_count': completed_count, 'overdue_steps': overdue_steps,
            'overdue_count': len(overdue_steps), 'total_time': total_time})
        total_open_steps += len(open_steps)
        total_overdue += len(overdue_steps)
    html = render_template('reports/team_pdf.html', team_data=team_data,
        total_open_steps=total_open_steps, total_overdue=total_overdue,
        report_date=datetime.utcnow())
    pdf = weasyprint.HTML(string=html, base_url='/').write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=raport_zespolowy.pdf'
    return response
