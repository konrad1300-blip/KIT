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
    # For admin: show all non-admin users
    # For non-admin: show only current user to avoid exposing others' data
    if current_user.has_role('admin'):
        # Get all non-admin users
        from app.models.role import Role
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            users = User.query.filter(~User.roles.any(id=admin_role.id)).all()
        else:
            users = User.query.all()
    else:
        users = [current_user]
    
    team_data = []
    total_open_steps = total_overdue = 0
    for user in users:
        # Get user's open steps (not completed)
        open_steps = Step.query.filter_by(assigned_to=user.id).filter(Step.status != 'completed').all()
        completed_steps = Step.query.filter_by(assigned_to=user.id, status='completed').all()
        
        # Calculate metrics
        total_assigned = len(open_steps) + len(completed_steps)
        total_estimated_open = sum(s.estimated_time or 0 for s in open_steps)
        total_actual_open = sum(s.actual_time or 0 for s in open_steps)
        total_completed_steps = len(completed_steps)
        
        # Get overdue steps (due_date < now AND not completed)
        from datetime import datetime
        overdue_steps = Step.query.filter(
            Step.assigned_to == user.id,
            Step.due_date < datetime.utcnow(),
            Step.status != 'completed'
        ).all()
        
        # Calculate utilization (assuming 8 hours per day = 480 minutes per day)
        # For simplicity, we'll use a weekly capacity of 40 hours = 2400 minutes
        weekly_capacity = 2400  # minutes per week
        utilization_percentage = min((total_estimated_open / weekly_capacity) * 100, 100) if weekly_capacity > 0 else 0
        
        team_data.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'roles': [role.to_dict() for role in user.roles],
            'role_names': user.get_roles_list(),
            'open_steps_count': len(open_steps),
            'completed_steps_count': total_completed_steps,
            'total_assigned': total_assigned,
            'total_estimated_open_minutes': total_estimated_open,
            'total_actual_open_minutes': total_actual_open,
            'utilization_percentage': round(utilization_percentage, 1),
            'is_overloaded': utilization_percentage > 80,  # Flag if over 80% utilization
            'overdue_count': len(overdue_steps)
        })
        total_open_steps += len(open_steps)
        total_overdue += len(overdue_steps)
    
    return jsonify({
        'team_members': team_data,
        'total_team_size': len(users),
        'total_open_steps': total_open_steps,
        'total_estimated_minutes': sum(item['total_estimated_open_minutes'] for item in team_data),
        'total_overdue': total_overdue
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

@dashboard_bp.route('/api/cumulative-flow')
@login_required
def api_cumulative_flow():
    """API endpoint for cumulative flow chart data"""
    # Get status counts for all steps (or for current user if not admin)
    if current_user.has_role('admin'):
        steps = Step.query.all()
    else:
        steps = Step.query.filter_by(assigned_to=current_user.id).all()
    
    # Count by status
    pending_count = sum(1 for s in steps if s.status == 'pending')
    in_progress_count = sum(1 for s in steps if s.status == 'in_progress')
    completed_count = sum(1 for s in steps if s.status == 'completed')
    
    # Build last 7 days data (simplified - showing current snapshot repeated)
    import datetime
    today = datetime.date.today()
    labels = [(today - datetime.timedelta(days=i)).strftime('%d.%m') for i in range(6, -1, -1)]
    
    return jsonify({
        'labels': labels,
        'datasets': [
            {
                'label': 'Do zrobienia',
                'data': [pending_count] * 7,
                'borderColor': 'rgba(255, 99, 132, 1)',
                'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                'fill': False
            },
            {
                'label': 'W trakcie',
                'data': [in_progress_count] * 7,
                'borderColor': 'rgba(54, 162, 235, 1)',
                'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                'fill': False
            },
            {
                'label': 'Zakończone',
                'data': [completed_count] * 7,
                'borderColor': 'rgba(75, 192, 192, 1)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                'fill': False
            }
        ]
    })

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard page"""
    return render_template('dashboard/analytics.html')