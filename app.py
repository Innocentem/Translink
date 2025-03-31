from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from datetime import timedelta
import os
from models import db, User  # Ensure User is imported here
from routes import auth_routes, dashboard_routes, browse_routes

# Initialize extensions
migrate = Migrate()
login_manager = LoginManager()

# Application factory function
def create_app():
    app = Flask(__name__)

    # App configuration
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///translink.db'
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit to 16 MB


    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth_routes.login'  # Reference to login route

    # Login Manager
    @login_manager.user_loader
    def load_user(user_id):
        # Simply return the user from the existing session managed by Flask-SQLAlchemy
        return User.query.get(int(user_id))

    # Register Blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(dashboard_routes)
    app.register_blueprint(browse_routes)

    return app

# Main entry point to run the app
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
