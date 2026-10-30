from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config
import os
import json

# Import extensions from extensions.py
from app.extensions import db, login_manager, csrf

def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.jinja_env.globals['json'] = json
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader for Flask-Login
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.profile import profile_bp
    from app.routes.resume import resume_bp
    from app.routes.opportunities import opportunities_bp
    from app.routes.recommendations import recommendations_bp
    from app.routes.applications import applications_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(resume_bp, url_prefix='/resume')
    app.register_blueprint(opportunities_bp, url_prefix='/opportunities')
    app.register_blueprint(recommendations_bp, url_prefix='/recommendations')
    app.register_blueprint(applications_bp, url_prefix='/applications')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Error handlers
    from app.routes.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    return app
