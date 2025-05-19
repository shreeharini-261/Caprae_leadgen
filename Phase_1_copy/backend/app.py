from flask import Flask, has_request_context, g
from models.lead_model import db
from routes.lead_routes import lead_bp
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from config.config import config
from flask_login import LoginManager, current_user
from models.user_model import User
from sqlalchemy import event, text


def create_app(config_class=config):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    def set_app_user_on_connect(dbapi_connection, connection_record):
        try:
            # Only set if in a request context and user is authenticated
            if has_request_context() and current_user.is_authenticated:
                username = getattr(current_user, 'username', None)
                if username:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("SELECT set_app_user(%s);", (username, ))
                    cursor.close()
        except Exception:
            pass  # Ignore if user is not available (e.g., during migrations)

    @app.before_request
    def set_audit_user():
        if has_request_context() and current_user.is_authenticated:
            username = getattr(current_user, 'username', None)
            if username:
                # Use the current session, not a new engine connection
                db.session.execute(text("SELECT set_app_user(:username);"),
                                   {"username": username})

    # Register blueprints
    app.register_blueprint(main_bp)  # Register main routes first
    app.register_blueprint(auth_bp)  # Register auth routes
    app.register_blueprint(lead_bp)  # Then register other routes

    # Create database tables
    with app.app_context():
        db.create_all()
        event.listen(db.engine, "connect", set_app_user_on_connect)

        # Call the audit log setup from the model
        from models.audit_log_model import ensure_audit_log_infrastructure
        ensure_audit_log_infrastructure(db)

    return app


# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
