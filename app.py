from flask import Flask, render_template, flash, redirect, request, session
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
import os
from dotenv import load_dotenv
from extensions import db, migrate, login_manager
from routes import auth_routes, dashboard_routes, browse_routes, admin_routes
from models import User

load_dotenv()

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    # Basic configuration from environment variables
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        WTF_CSRF_SECRET_KEY=os.getenv('CSRF_SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL'),
        UPLOAD_FOLDER=os.getenv('UPLOAD_FOLDER'),
        MAX_CONTENT_LENGTH=int(os.getenv('MAX_CONTENT_LENGTH')),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=True,
        UPLOAD_EXTENSIONS=['.jpg', '.png', '.jpeg']
    )

    # Session configuration
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=int(os.getenv('SESSION_LIFETIME')))
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=int(os.getenv('REMEMBER_DURATION')))

    # Security headers
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_SECURE=True,
        REMEMBER_COOKIE_HTTPONLY=True
    )

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth_routes.landing'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.refresh_view = 'auth_routes.landing'
    login_manager.needs_refresh_message = 'Please log in again to confirm your identity.'
    login_manager.needs_refresh_message_category = 'info'
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):
        if user_id is None:
            return None
        try:
            return db.session.get(User, int(user_id))
        except Exception as e:
            print(f"Error loading user: {str(e)}")
            return None

    # Register blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(dashboard_routes)
    app.register_blueprint(browse_routes)
    app.register_blueprint(admin_routes)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def too_large(error):
        flash('File is too large. Maximum size is 16MB.', 'danger')
        return redirect(request.url), 413

    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=int(os.getenv('SESSION_LIFETIME')))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
