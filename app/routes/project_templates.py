from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.project_template import ProjectTemplate
from app.models.step_template import StepTemplate
from app.models.project import Project
from app.models.step import Step
from app.models.user import User
from app.models.log import Log
from datetime import datetime

project_templates_bp = Blueprint('project_templates', __name__, url_prefix='/project-templates')

@project_templates_bp.route('/')
@login_required
def list_templates():
    """List all project templates (admin only)"""
    if current_user.role != 'admin':
        flash('Tylko administrator może zarządzać szablonami projektów.', 'error')
        return redirect(url_for('dashboard.index'))
    
    templates = ProjectTemplate.query.filter_by(is_active=True).order_by(ProjectTemplate.name).all()
    return render_template('project_templates/list.html', templates=templates)

@project_templates_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create new project template (admin only)"""
    if current_user.role != 'admin':
        flash('Tylko administrator może tworzyć szablony projektów.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        step_template_ids = request.form.getlist('step_templates')
        
        # Validation
        if not name:
            flash('Nazwa szablonu jest wymagana.', 'error')
            return redirect(url_for('project_templates.create_template'))
        
        if ProjectTemplate.query.filter_by(name=name).first():
            flash('Szablon o tej nazwie już istnieje.', 'error')
            return redirect(url_for('project_templates.create_template'))
        
        # Create template
        template = ProjectTemplate(
            name=name,
            description=description,
            created_by=current_user.id
        )
        
        # Add step templates
        if step_template_ids:
            step_templates = StepTemplate.query.filter(StepTemplate.id.in_(step_template_ids)).all()
            template.step_templates.extend(step_templates)
        
        db.session.add(template)
        
        # Log action
        log = Log(
            user_id=current_user.id,
            action='create_project_template',
            resource_type='project_template',
            details=f'Created project template: {name}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Szablon projektu "{name}" został utworzony!', 'success')
        return redirect(url_for('project_templates.list_templates'))
    
    step_templates = StepTemplate.query.filter_by(is_active=True).order_by(StepTemplate.name).all()
    return render_template('project_templates/form.html', template=None, step_templates=step_templates)

@project_templates_bp.route('/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    """Edit project template (admin only)"""
    if current_user.role != 'admin':
        flash('Tylko administrator może edytować szablony projektów.', 'error')
        return redirect(url_for('dashboard.index'))
    
    template = ProjectTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        step_template_ids = request.form.getlist('step_templates')
        is_active = 'is_active' in request.form
        
        # Validation
        if not name:
            flash('Nazwa szablonu jest wymagana.', 'error')
            return redirect(url_for('project_templates.edit_template', template_id=template_id))
        
        # Check if another template with this name exists (excluding current template)
        existing_template = ProjectTemplate.query.filter(ProjectTemplate.name == name, ProjectTemplate.id != template_id).first()
        if existing_template:
            flash('Szablon o tej nazwie już istnieje.', 'error')
            return redirect(url_for('project_templates.edit_template', template_id=template_id))
        
        # Update template
        template.name = name
        template.description = description
        template.is_active = is_active
        
        # Update step templates
        template.step_templates = []  # Clear existing
        if step_template_ids:
            step_templates = StepTemplate.query.filter(StepTemplate.id.in_(step_template_ids)).all()
            template.step_templates.extend(step_templates)
        
        # Log action
        log = Log(
            user_id=current_user.id,
            action='update_project_template',
            resource_type='project_template',
            resource_id=template.id,
            details=f'Updated project template: {name}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Szablon projektu "{name}" został zaktualizowany!', 'success')
        return redirect(url_for('project_templates.list_templates'))
    
    step_templates = StepTemplate.query.filter_by(is_active=True).order_by(StepTemplate.name).all()
    return render_template('project_templates/form.html', template=template, step_templates=step_templates)

@project_templates_bp.route('/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    """Delete project template (admin only)"""
    if current_user.role != 'admin':
        flash('Tylko administrator może usuwać szablony projektów.', 'error')
        return redirect(url_for('dashboard.index'))
    
    template = ProjectTemplate.query.get_or_404(template_id)
    template_name = template.name
    
    # Soft delete - mark as inactive
    template.is_active = False
    
    # Log action
    log = Log(
        user_id=current_user.id,
        action='delete_project_template',
        resource_type='project_template',
        resource_id=template.id,
        details=f'Deleted project template: {template_name}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Szablon projektu "{template_name}" został usunięty!', 'success')
    return redirect(url_for('project_templates.list_templates'))

@project_templates_bp.route('/<int:template_id>/create-project', methods=['POST'])
@login_required
def create_project_from_template(template_id):
    """Create a new project from a template (admin only)"""
    if current_user.role != 'admin':
        flash('Tylko administrator może tworzyć projekty na podstawie szablonów.', 'error')
        return redirect(url_for('dashboard.index'))
    
    template = ProjectTemplate.query.get_or_404(template_id)
    
    # Create project
    project = Project(
        name=template.name + " - Kopia",  # Default name, user can change later
        description=template.description,
        priority=2,  # Default priority
        created_by=current_user.id
    )
    
    db.session.add(project)
    db.session.flush()  # To get the project ID
    
    # Create steps from the step templates in the project template
    for step_template in template.step_templates:
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
    
    # Log action
    log = Log(
        user_id=current_user.id,
        action='create_project_from_template',
        resource_type='project',
        resource_id=project.id,
        details=f'Created project from template: {template.name}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Projekt "{project.name}" został utworzony na podstawie szablonu "{template.name}"!', 'success')
    return redirect(url_for('projects.view_project', project_id=project.id))

@project_templates_bp.route('/api/<int:template_id>')
@login_required
def get_template_api(template_id):
    """Get template data as API for AJAX calls"""
    template = ProjectTemplate.query.get_or_404(template_id)
    return jsonify(template.to_dict())