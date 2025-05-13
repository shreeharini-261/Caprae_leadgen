from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import text

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main landing page"""
    return render_template('index.html')

@main_bp.route('/docs/user')
@login_required
def user_docs():
    """Render the user documentation page"""
    return render_template('docs/user_docs.html')

@main_bp.route('/docs/admin')
@login_required
def admin_docs():
    """Render the admin documentation page - only accessible to admins and developers"""
    if current_user.role not in ['admin', 'developer']:
        return render_template('errors/403.html'), 403
    return render_template('docs/admin_docs.html')

@main_bp.route('/audit_log')
@login_required
def audit_log():
    if current_user.role not in ['admin', 'developer']:
        return render_template('errors/403.html'), 403

    # Simple filter: by username or column name
    username = request.args.get('username', '').strip()
    column = request.args.get('column', '').strip()
    limit = int(request.args.get('limit', 100))

    query = '''SELECT id, table_name, row_id, column_name, old_value, new_value, username, changed_at
               FROM lead_audit_log WHERE 1=1'''
    params = {}
    if username:
        query += ' AND username ILIKE :username'
        params['username'] = f'%{username}%'
    if column:
        query += ' AND column_name ILIKE :column'
        params['column'] = f'%{column}%'
    query += ' ORDER BY changed_at DESC LIMIT :limit'
    params['limit'] = limit

    from models.lead_model import db
    logs = []
    with db.engine.connect() as conn:
        result = conn.execute(text(query), params)
        for row in result:
            logs.append(dict(row._mapping))

    return render_template('audit_log.html', logs=logs, username=username, column=column, limit=limit) 