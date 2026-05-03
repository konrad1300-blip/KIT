from flask import Blueprint, render_template, make_response, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Project, Step, User, Role
from app import db
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

# Direct access blueprint (no URL prefix) - for routes like /project/1/pdf, /user/2/weekly-pdf, /team/pdf
direct_bp = Blueprint('direct', __name__)

@direct_bp.route('/project/<int:project_id>/pdf')
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

@direct_bp.route('/user/<int:user_id>/weekly-pdf')
@login_required
def user_weekly_pdf(user_id):
    import weasyprint
    user = User.query.get_or_404(user_id)
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

@direct_bp.route('/user/<int:user_id>/monthly-pdf')
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

@direct_bp.route('/team/pdf')
@login_required
def team_pdf():
    import weasyprint
    if not current_user.has_role('admin'):
        flash('Tylko administrator może generować raporty zespołowe.', 'error')
        return redirect(url_for('dashboard.index'))
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

@reports_bp.route('/project/<int:project_id>/pdf')
@login_required
def project_pdf_reports(project_id):
    return project_pdf(project_id)

@reports_bp.route('/user/<int:user_id>/weekly-pdf')
@login_required
def user_weekly_pdf_reports(user_id):
    return user_weekly_pdf(user_id)

@reports_bp.route('/user/<int:user_id>/monthly-pdf')
@login_required
def user_monthly_pdf_reports(user_id):
    return user_monthly_pdf(user_id)

@reports_bp.route('/team/pdf')
@login_required
def team_pdf_reports():
    return team_pdf()

@reports_bp.route('/')
@login_required
def index():
    if not current_user.has_role('admin'):
        flash('Tylko administrator może przeglądać raporty.', 'error')
        return redirect(url_for('dashboard.index'))
    from app.models.role import Role
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_role:
        users = User.query.filter(~User.roles.any(id=admin_role.id)).all()
    else:
        users = User.query.all()
    return render_template('reports/index.html', users=users)