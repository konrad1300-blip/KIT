import json
from datetime import datetime
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models import Project, Step, Notification, User
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    # Get user's assigned steps
    user_steps = Step.query.filter_by(assigned_to=current_user.id).all()

    # Get all active projects
    projects = Project.query.filter_by(status='active').all()

    # Get statistics
    stats = {
        'total_steps': Step.query.count(),
        'my_steps': len(user_steps),
        'pending': Step.query.filter_by(status='pending').count(),
        'in_progress': Step.query.filter_by(status='in_progress').count(),
        'completed': Step.query.filter_by(status='completed').count(),
        'active_projects': Project.query.filter_by(status='active').count(),
        'my_pending': Step.query.filter_by(assigned_to=current_user.id, status='pending').count(),
        'my_in_progress': Step.query.filter_by(assigned_to=current_user.id, status='in_progress').count(),
        'my_completed': Step.query.filter_by(assigned_to=current_user.id, status='completed').count(),
    }

    # Get recent steps (last 10)
    recent_steps = Step.query.order_by(Step.created_at.desc()).limit(10).all()

    # Get overdue steps
    from datetime import datetime
    overdue_steps = Step.query.filter(
        Step.due_date < datetime.utcnow(),
        Step.status != 'completed'
    ).all()

    # Get high priority steps
    high_priority_steps = Step.query.filter(
        Step.priority.in_(['urgent', 'very_urgent']),
        Step.status != 'completed'
    ).order_by(Step.due_date.asc()).limit(5).all()

    # Project completion stats
    project_stats = []
    for project in projects:
        project_stats.append({
            'project': project,
            'total_steps': project.steps.count(),
            'completed': project.steps.filter_by(status='completed').count(),
            'in_progress': project.steps.filter_by(status='in_progress').count(),
            'completion_percentage': project.completion_percentage
        })

    return render_template('dashboard/index.html',
                         stats=stats,
                         recent_steps=recent_steps,
                         overdue_steps=overdue_steps,
                         high_priority_steps=high_priority_steps,
                         project_stats=project_stats,
                         user_steps=user_steps)

@dashboard_bp.route('/api/team-load')
@login_required
def api_team_load():
    """API endpoint for team load data"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get all non-admin users
    users = User.query.filter(User.role != 'admin').all()
    team_data = []
    
    for user in users:
        # Get user's open steps (not completed)
        open_steps = Step.query.filter_by(assigned_to=user.id).filter(Step.status != 'completed').all()
        completed_steps = Step.query.filter_by(assigned_to=user.id, status='completed').all()
        
        # Calculate metrics
        total_assigned = len(open_steps) + len(completed_steps)
        total_estimated_open = sum(s.estimated_time for s in open_steps)
        total_actual_open = sum(s.actual_time for s in open_steps)
        total_completed_steps = len(completed_steps)
        
        # Calculate utilization (assuming 8 hours per day = 480 minutes per day)
        # For simplicity, we'll use a weekly capacity of 40 hours = 2400 minutes
        weekly_capacity = 2400  # minutes per week
        utilization_percentage = min((total_estimated_open / weekly_capacity) * 100, 100) if weekly_capacity > 0 else 0
        
        team_data.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'open_steps_count': len(open_steps),
            'completed_steps_count': total_completed_steps,
            'total_assigned': total_assigned,
            'total_estimated_open_minutes': total_estimated_open,
            'total_actual_open_minutes': total_actual_open,
            'utilization_percentage': round(utilization_percentage, 1),
            'is_overloaded': utilization_percentage > 80  # Flag if over 80% utilization
        })
    
    return jsonify({
        'team_members': team_data,
        'total_team_size': len(users),
        'total_open_steps': sum(item['open_steps_count'] for item in team_data),
        'total_estimated_minutes': sum(item['total_estimated_open_minutes'] for item in team_data)
    })

@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for analytics statistics"""
    from datetime import datetime
    
    # All overdue high priority steps
    all_overdue_high = Step.query.filter(
        Step.due_date < datetime.utcnow(),
        Step.status != 'completed',
        Step.priority.in_(['urgent', 'very_urgent'])
    ).all()
    
    # Current user's stats
    user_pending = Step.query.filter_by(assigned_to=current_user.id, status='pending').count()
    user_in_progress = Step.query.filter_by(assigned_to=current_user.id, status='in_progress').count()
    user_completed = Step.query.filter_by(assigned_to=current_user.id, status='completed').count()
    
    # Overall project status counts
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='active').count()
    completed_projects = Project.query.filter_by(status='completed').count()
    
    return jsonify({
        'bottleneck_count': len(all_overdue_high),
        'user_stats': {
            'pending': user_pending,
            'in_progress': user_in_progress,
            'completed': user_completed
        },
        'project_stats': {
            'total': total_projects,
            'active': active_projects,
            'completed': completed_projects
        },
        'overdue_high_priority_tasks': [{
            'id': s.id,
            'name': s.name,
            'project': s.project.name if s.project else None,
            'assigned_to': s.assignee.full_name if s.assignee else None,
            'due_date': s.due_date.isoformat() if s.due_date else None,
            'priority': s.priority,
            'status': s.status
        } for s in all_overdue_high]
    })

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard page"""
    return render_template('dashboard/analytics.html')