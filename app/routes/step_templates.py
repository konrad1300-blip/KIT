from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.step_template import StepTemplate
from app.models.skill import Skill
from app.models.user import User
from app.models.log import Log
from datetime import datetime

step_templates_bp = Blueprint('step_templates', __name__, url_prefix='/step-templates')

@step_templates_bp.route('/')
@login_required
def list_templates():
    """List all step templates (admin only)"""
    if current_user.role != 'admin':
        flash('Tylko administrator może zarządzać szablonami kroków.', 'error')
        return redirect(url_for('dashboard.index'))
    
    templates = StepTemplate.query.filter_by(is_active=True).order_by(StepTemplate.name).all()
    return render_template('step_templates/list.html', templates=templates)

@step_templates_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create new step template (admin only)"""
    if current_user.role != 'admin':
        flash('Tylko administrator może tworzyć szablony kroków.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        step_type = request.form.get('step_type')
        priority = request.form.get('priority', 'normal')
        estimated_time = request.form.get('estimated_time', type=int)
        skill_ids = request.form.getlist('skills')
        
        # Validation
        if not name:
            flash('Nazwa szablonu jest wymagana.', 'error')
            return redirect(url_for('step_templates.create_template'))
        
        if StepTemplate.query.filter_by(name=name).first():
            flash('Szablon o tej nazwie już istnieje.', 'error')
            return redirect(url_for('step_templates.create_template'))
        
        # Create template
        template = StepTemplate(
            name=name,
            description=description,
            step_type=step_type,
            priority=priority,
            estimated_time=estimated_time,
            created_by=current_user.id
        )
        
        # Add skills
        if skill_ids:
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            template.required_skills.extend(skills)
        
        db.session.add(template)
        
        # Log action
        log = Log(
            user_id=current_user.id,
            action='create_step_template',
            resource_type='step_template',
            details=f'Created step template: {name}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Szablon kroku "{name}" został utworzony!', 'success')
        return redirect(url_for('step_templates.list_templates'))
    
    skills = Skill.query.all()
    return render_template('step_templates/form.html', template=None, skills=skills)

@step_templates_bp.route('/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    """Edit step template (admin only)"""
    if current_user.role != 'admin':
        flash('Tylko administrator może edytować szablony kroków.', 'error')
        return redirect(url_for('dashboard.index'))
    
    template = StepTemplate.query.get_or_404(template_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        step_type = request.form.get('step_type')
        priority = request.form.get('priority', 'normal')
        estimated_time = request.form.get('estimated_time', type=int)
        skill_ids = request.form.getlist('skills')
        is_active = 'is_active' in request.form
        
        # Validation
        if not name:
            flash('Nazwa szablonu jest wymagana.', 'error')
            return redirect(url_for('step_templates.edit_template', template_id=template_id))
        
        # Check if another template with this name exists (excluding current template)
        existing_template = StepTemplate.query.filter(StepTemplate.name == name, StepTemplate.id != template_id).first()
        if existing_template:
            flash('Szablon o tej nazwie już istnieje.', 'error')
            return redirect(url_for('step_templates.edit_template', template_id=template_id))
        
        # Update template
        template.name = name
        template.description = description
        template.step_type = step_type
        template.priority = priority
        template.estimated_time = estimated_time
        template.is_active = is_active
        
        # Update skills
        template.required_skills = []  # Clear existing
        if skill_ids:
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            template.required_skills.extend(skills)
        
        # Log action
        log = Log(
            user_id=current_user.id,
            action='update_step_template',
            resource_type='step_template',
            resource_id=template.id,
            details=f'Updated step template: {name}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Szablon kroku "{name}" został zaktualizowany!', 'success')
        return redirect(url_for('step_templates.list_templates'))
    
    skills = Skill.query.all()
    return render_template('step_templates/form.html', template=template, skills=skills)

@step_templates_bp.route('/<int:template_id>/delete', methods=['POST'])
@login_required
def delete_template(template_id):
    """Delete step template (admin only)"""
    if current_user.role != 'admin':
        flash('Tylko administrator może usuwać szablony kroków.', 'error')
        return redirect(url_for('dashboard.index'))
    
    template = StepTemplate.query.get_or_404(template_id)
    template_name = template.name
    
    # Soft delete - mark as inactive
    template.is_active = False
    
    # Log action
    log = Log(
        user_id=current_user.id,
        action='delete_step_template',
        resource_type='step_template',
        resource_id=template.id,
        details=f'Deleted step template: {template_name}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Szablon kroku "{template_name}" został usunięty!', 'success')
    return redirect(url_for('step_templates.list_templates'))

@step_templates_bp.route('/api/<int:template_id>')
@login_required
def get_template_api(template_id):
    """Get template data as API for AJAX calls"""
    template = StepTemplate.query.get_or_404(template_id)
    return jsonify(template.to_dict())