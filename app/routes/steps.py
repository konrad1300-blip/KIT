from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.step import Step
from app.models.project import Project
from app.models.user import User
from app.models.skill import Skill
from app.models.log import Log
from app.models.notification import Notification
from app.models.comment import Comment
from app.models.step_template import StepTemplate
from datetime import datetime

steps_bp = Blueprint('steps', __name__)

@steps_bp.route('/')
@login_required
def list_steps():
    """List all steps with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Step.query

    # Filter by assigned user (for non-admin users)
    if current_user.role != 'admin':
        query = query.filter_by(assigned_to=current_user.id)
    # Filter by assigned user (for admin users)
    else:
        assigned_to = request.args.get('assigned_to', type=int)
        if assigned_to:
            query = query.filter_by(assigned_to=assigned_to)

    # Filter by status
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    # Filter by project
    project_id = request.args.get('project_id', type=int)
    if project_id:
        query = query.filter_by(project_id=project_id)

    # Filter by priority
    priority = request.args.get('priority')
    if priority:
        query = query.filter_by(priority=priority)

    # Filter by date range
    date_from = request.args.get('date_from')
    if date_from:
        from_date = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Step.due_date >= from_date)

    date_to = request.args.get('date_to')
    if date_to:
        to_date = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(Step.due_date <= to_date)

    # Filter by overdue
    if request.args.get('overdue') == '1':
        query = query.filter(Step.due_date < datetime.utcnow(), Step.status != 'completed')

    # Search
    search = request.args.get('search')
    if search:
        query = query.filter(Step.name.ilike(f'%{search}%'))

    # Sorting
    sort_by = request.args.get('sort', 'due_date')
    sort_order = request.args.get('order', 'asc')

    if sort_by == 'priority':
        priority_order = db.case(
            (Step.priority == 'very_urgent', 0),
            (Step.priority == 'urgent', 1),
            (Step.priority == 'high', 2),
            (Step.priority == 'normal', 3),
            else_=4
        )
        if sort_order == 'asc':
            query = query.order_by(priority_order.asc())
        else:
            query = query.order_by(priority_order.desc())
    elif sort_by == 'due_date':
        if sort_order == 'asc':
            query = query.order_by(Step.due_date.asc())
        else:
            query = query.order_by(Step.due_date.desc())
    elif sort_by == 'created_at':
        if sort_order == 'asc':
            query = query.order_by(Step.created_at.asc())
        else:
            query = query.order_by(Step.created_at.desc())
    else:
        query = query.order_by(Step.priority.desc(), Step.due_date.asc())

    steps = query.paginate(page=page, per_page=per_page, error_out=False)

    # Get filter options
    projects = Project.query.all()
    users = User.query.all() if current_user.role == 'admin' else [current_user]

    stats = {
        'total': Step.query.count(),
        'pending': Step.query.filter_by(status='pending').count(),
        'in_progress': Step.query.filter_by(status='in_progress').count(),
        'completed': Step.query.filter_by(status='completed').count(),
    }

    return render_template('steps/list.html', steps=steps, projects=projects, users=users, stats=stats, filters=request.args)

@steps_bp.route('/<int:step_id>')
@login_required
def view_step(step_id):
    """View single step details"""
    step = Step.query.get_or_404(step_id)

    if current_user.role != 'admin' and step.assigned_to != current_user.id:
        flash('Nie masz uprawnień do przeglądania tego kroku.', 'error')
        return redirect(url_for('steps.list_steps'))

    sorted_comments = step.comments.order_by(Comment.created_at.desc()).all()
    return render_template('steps/view.html', step=step, sorted_comments=sorted_comments)

@steps_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_step():
    if request.method == 'POST':
        return _save_step(None)
    return _show_create_form()

@steps_bp.route('/<int:step_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_step(step_id):
    step = Step.query.get_or_404(step_id)

    if current_user.role != 'admin' and step.assigned_to != current_user.id and step.created_by != current_user.id:
        flash('Nie masz uprawnień do edycji tego kroku.', 'error')
        return redirect(url_for('steps.list_steps'))

    if request.method == 'POST':
        return _save_step(step_id)

    return _show_edit_form(step_id)

def _save_step(step_id):
    name = request.form.get('name')
    description = request.form.get('description')
    step_type = request.form.get('step_type')
    assigned_to = request.form.get('assigned_to', type=int)
    estimated_time = request.form.get('estimated_time', type=int)
    due_date_str = request.form.get('due_date')
    priority = request.form.get('priority', 'normal')
    status = request.form.get('status', 'pending')
    notes = request.form.get('notes')
    project_id = request.form.get('project_id', type=int)

    if not name:
        flash('Nazwa kroku jest wymagana.', 'error')
        return redirect(url_for('steps.create_step') if not step_id else url_for('steps.edit_step', step_id=step_id))

    # Validate assigned user has required skills for this step type
    if assigned_to and step_type:
        from app.models.user import User
        assignee = User.query.get(assigned_to)
        if assignee:
            # Create a temporary step to check skills
            temp_step = Step(step_type=step_type)
            if not temp_step.can_user_execute(assignee):
                flash(f'Użytkownik {assignee.full_name} nie posiada wymaganych umiejętności dla tego typu zadania.', 'error')
                return redirect(url_for('steps.create_step') if not step_id else url_for('steps.edit_step', step_id=step_id))

    if step_id:
        step = Step.query.get_or_404(step_id)
        old_assigned_to = step.assigned_to
    else:
        step = Step(created_by=current_user.id)
        old_assigned_to = None

    step.name = name
    step.description = description
    step.step_type = step_type
    step.assigned_to = assigned_to
    step.estimated_time = estimated_time
    step.priority = priority
    step.status = status
    step.notes = notes

    if due_date_str:
        step.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
    else:
        step.due_date = None

    if project_id:
        step.project_id = project_id

    if step_id:
        db.session.add(step)
    else:
        db.session.add(step)
        db.session.flush()

    if step.project_id:
        _update_project_status(step.project_id)

    if step.assigned_to and step.assigned_to != old_assigned_to:
        notification = Notification(
            user_id=step.assigned_to,
            title='Zadanie przypisane',
            message=f'Zostałeś przypisany do kroku: {step.name}',
            notification_type='assignment',
            link=url_for('steps.view_step', step_id=step.id)
        )
        db.session.add(notification)

    action = 'update_step' if step_id else 'create_step'
    log = Log(
        user_id=current_user.id,
        action=action,
        resource_type='step',
        resource_id=step.id,
        details=f'{action.capitalize()}: {name}'
    )
    db.session.add(log)

    db.session.commit()
    flash(f'Krok został {"zaktualizowany" if step_id else "utworzony"}!', 'success')

    return redirect(url_for('steps.view_step', step_id=step.id) if step_id else url_for('projects.view_project', project_id=step.project_id) if step.project_id else url_for('steps.list_steps'))

def _update_project_status(project_id):
    project = Project.query.get(project_id)
    if not project:
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
    # If no steps are in progress and not all completed, status remains as is

    # Note: Commit is handled by the calling function

def _show_create_form():
    projects = Project.query.all()
    users = User.query.all()
    skills = Skill.query.all()
    templates = StepTemplate.query.filter_by(is_active=True).order_by(StepTemplate.name).all()
    return render_template('steps/form.html', step=None, projects=projects, users=users, skills=skills, templates=templates)

def _show_edit_form(step_id):
    step = Step.query.get_or_404(step_id)
    projects = Project.query.all()
    users = User.query.all()
    skills = Skill.query.all()
    templates = StepTemplate.query.filter_by(is_active=True).order_by(StepTemplate.name).all()
    return render_template('steps/form.html', step=step, projects=projects, users=users, skills=skills, templates=templates)

@steps_bp.route('/<int:step_id>/delete', methods=['POST'])
@login_required
def delete_step(step_id):
    step = Step.query.get_or_404(step_id)

    if current_user.role != 'admin' and step.created_by != current_user.id:
        flash('Nie masz uprawnień do usunięcia tego kroku.', 'error')
        return redirect(url_for('steps.list_steps'))

    project_id = step.project_id
    step_name = step.name

    log = Log(
        user_id=current_user.id,
        action='delete_step',
        resource_type='step',
        details=f'Deleted step: {step_name}'
    )
    db.session.add(log)

    db.session.delete(step)
    db.session.commit()

    if project_id:
        _update_project_status(project_id)

    flash('Krok został usunięty!', 'success')
    return redirect(url_for('projects.view_project', project_id=project_id) if project_id else url_for('steps.list_steps'))

@steps_bp.route('/<int:step_id>/status/<string:status>', methods=['POST'])
@login_required
def change_status(step_id, status):
    step = Step.query.get_or_404(step_id)

    if current_user.role != 'admin' and step.assigned_to != current_user.id:
        flash('Nie masz uprawnień do zmiany statusu tego kroku.', 'error')
        return redirect(url_for('steps.list_steps'))

    old_status = step.status

    if status == 'complete':
        step.mark_completed()
    elif status == 'progress':
        step.mark_in_progress()
    elif status == 'pending':
        step.mark_pending()
    else:
        flash('Nieprawidłowy status.', 'error')
        return redirect(url_for('steps.view_step', step_id=step.id))

    project_id = step.project_id
    if step.project_id:
        _update_project_status(step.project_id)

    log = Log(
        user_id=current_user.id,
        action='change_step_status',
        resource_type='step',
        resource_id=step.id,
        details=f'Changed status from {old_status} to {status}'
    )
    db.session.add(log)

    try:
        db.session.commit()
        flash(f'Status zmieniony na {"Zakończone" if status == "complete" else "W trakcie" if status == "progress" else "Do zrobienia"}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Wystąpił błąd podczas zapisywania: {str(e)}', 'error')

    return redirect(request.referrer or url_for('steps.view_step', step_id=step.id))

@steps_bp.route('/<int:step_id>/comment', methods=['POST'])
@login_required
def add_comment(step_id):
    """Add comment to step"""
    step = Step.query.get_or_404(step_id)

    content = request.form.get('content')
    if not content:
        flash('Komentarz nie może być pusty.', 'error')
        return redirect(url_for('steps.view_step', step_id=step.id))

    comment = Comment(
        step_id=step.id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(comment)

    if step.assigned_to and step.assigned_to != current_user.id:
        notification = Notification(
            user_id=step.assigned_to,
            title='Nowy komentarz',
            message=f'Dodano nowy komentarz do: {step.name}',
            notification_type='comment',
            link=url_for('steps.view_step', step_id=step.id)
        )
        db.session.add(notification)

    db.session.commit()
    flash('Komentarz został dodany!', 'success')
    return redirect(url_for('steps.view_step', step_id=step.id))