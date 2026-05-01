from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    """Reports dashboard - coming soon"""
    if current_user.role != 'admin':
        flash('Tylko administrator może generować raporty.', 'error')
        return redirect(url_for('dashboard.index'))
    
    return render_template('reports/index.html')