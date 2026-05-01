from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.project import Project
from app.models.step import Step
from app.models.project_template import ProjectTemplate
from app.models.step_template import StepTemplate
from app.models.log import Log
from app.models.notification import Notification
from datetime import datetime

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/')
@login_required
def list_projects():
    """List all projects"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Project.query

    # Filter by status if provided
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    # Search
    search = request.args.get('search')
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%'))

    projects = query.order_by(Project.priority.desc(), Project.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('projects/list.html', projects=projects)

@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_project():
    """Create new project"""
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
            name=name,
            description=description,
            priority=priority,
            created_by=current_user.id,
            project_template_id=project_template_id
        )

        if due_date_str:
            project.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')

        db.session.add(project)
        db.session.flush()  # To get the project ID

        # If a project template was selected, create steps from its step templates
        if project_template_id:
            project_template = ProjectTemplate.query.get(project_template_id)
            if project_template:
                for step_template in project_template.step_templates:
                    step = Step(
                        name=step_template.name,
                        description=step_template.description,
                        step_type=step_template.step_type,
                        priority=step_template.priority,
                        estimated_time=step_template.estimated_time,
                        project_id=project.id,
                        created_by=current_user.id,
                        template_id=step_template.id  # Link to the step template
                    )
                    db.session.add(step)
                    db.session.flush()  # To get step ID for notifications if needed

                    # Create notification for assigned user? Not at this stage, as steps are not assigned yet.
                    # We'll leave assignment to be done later when creating/editing steps.

        # Log action
        log = Log(
            user_id=current_user.id,
            action='create_project',
            resource_type='project',
            resource_id=project.id,
            details=f'Created project: {name}'
        )
        db.session.add(log)
        db.session.commit()

        flash('Projekt został utworzony!', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))

    # GET request: fetch project templates for admin users
    project_templates = None
    if current_user.role == 'admin':
        project_templates = ProjectTemplate.query.filter_by(is_active=True).order_by(ProjectTemplate.name).all()

    return render_template('projects/form.html', project=None, project_templates=project_templates)

@projects_bp.route('/<int:project_id>')
@login_required
def view_project(project_id):
    """View project details"""
    project = Project.query.get_or_404(project_id)
    steps = project.steps.order_by(Step.priority.desc(), Step.created_at).all()

    # Group steps by status
    steps_by_status = {
        'pending': [s for s in steps if s.status == 'pending'],
        'in_progress': [s for s in steps if s.status == 'in_progress'],
        'completed': [s for s in steps if s.status == 'completed']
    }

    return render_template('projects/view.html',
                         project=project,
                         steps_by_status=steps_by_status,
                         total_steps=len(steps),
                         completed_steps=len(steps_by_status['completed']))

@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Edit project"""
    if current_user.role != 'admin':
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

        # Log action
        log = Log(
            user_id=current_user.id,
            action='update_project',
            resource_type='project',
            resource_id=project.id,
            details=f'Updated project: {project.name}'
        )
        db.session.add(log)
        db.session.commit()

        flash('Projekt został zaktualizowany!', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))

    return render_template('projects/form.html', project=project)

@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Delete project"""
    if current_user.role != 'admin':
        flash('Tylko administrator może usuwać projekty.', 'error')
        return redirect(url_for('projects.list_projects'))

    project = Project.query.get_or_404(project_id)

    # Log action before delete
    log = Log(
        user_id=current_user.id,
        action='delete_project',
        resource_type='project',
        details=f'Deleted project: {project.name}'
    )
    db.session.add(log)

    db.session.delete(project)
    db.session.commit()

    flash('Projekt został usunięty!', 'success')
    return redirect(url_for('projects.list_projects'))

@projects_bp.route('/<int:project_id>/steps/create', methods=['GET', 'POST'])
@login_required
def create_step(project_id):
    """Create step for project"""
    project = Project.query.get_or_404(project_id)
    from app.models import User, Skill

    def _update_project_status(project_id):
        """Update project status based on its steps"""
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

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        step_type = request.form.get('step_type')
        assigned_to = request.form.get('assigned_to', type=int)
        estimated_time = request.form.get('estimated_time', type=int)
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'normal')
        notes = request.form.get('notes')

        if not name:
            flash('Nazwa kroku jest wymagana.', 'error')
            return redirect(url_for('projects.create_step', project_id=project.id))

        # Validate assigned user has required skills for this step type
        if assigned_to and step_type:
            from app.models.user import User
            assignee = User.query.get(assigned_to)
            if assignee:
                # Create a temporary step to check skills
                temp_step = Step(step_type=step_type)
                if not temp_step.can_user_execute(assignee):
                    flash(f'Użytkownik {assignee.full_name} nie posiada wymaganych umiejętności dla tego typu zadania.', 'error')
                    return redirect(url_for('projects.create_step', project_id=project.id))

        step = Step(
            name=name,
            description=description,
            step_type=step_type,
            assigned_to=assigned_to,
            created_by=current_user.id,
            estimated_time=estimated_time,
            priority=priority,
            project_id=project.id,
            notes=notes
        )

        if due_date_str:
            step.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')

        db.session.add(step)
        db.session.flush()

        # Create notification for assigned user
        if assigned_to:
            notification = Notification(
                user_id=assigned_to,
                title='Nowe zadanie przypisane',
                message=f'Zostałeś przypisany do kroku: {name}',
                notification_type='assignment',
                link=url_for('steps.edit_step', step_id=step.id)
            )
            db.session.add(notification)

        # Log action
        log = Log(
            user_id=current_user.id,
            action='create_step',
            resource_type='step',
            resource_id=step.id,
            details=f'Created step: {name} for project {project.name}'
        )
        db.session.add(log)
        
        # Update project status based on new step BEFORE commit
        _update_project_status(project.id)

        db.session.commit()

        flash('Krok został utworzony!', 'success')
        return redirect(url_for('projects.view_project', project_id=project.id))

    users = User.query.all()
    skills = Skill.query.all()
    return render_template('projects/create_step.html',
                         project=project,
                         users=users,
                         skills=skills)