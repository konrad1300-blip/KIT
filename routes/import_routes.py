from flask import Blueprint, render_template, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.import_export import (
    generate_projects_template,
    generate_steps_template,
    generate_users_template
)

import_bp = Blueprint('import', __name__)


@import_bp.route('/template/<type>')
@login_required
def download_template(type):
    """Pobierz szablon Excel do importu"""
    if not current_user.has_role('admin'):
        flash('Tylko administrator może pobierać szablony.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        if type == 'projects':
            output = generate_projects_template()
            filename = 'szablon_projektow.xlsx'
        elif type == 'steps':
            output = generate_steps_template()
            filename = 'szablon_zadan.xlsx'
        elif type == 'users':
            output = generate_users_template()
            filename = 'szablon_uzytkownikow.xlsx'
        else:
            flash('Nieznany typ szablonu.', 'error')
            return redirect(url_for('dashboard.index'))
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Błąd generowania szablonu: {str(e)}', 'error')
        return redirect(url_for('dashboard.index'))
