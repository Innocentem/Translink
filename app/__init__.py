from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Import models inside the function to avoid circular import
    from app.models import User

    # Register the user_loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.auth.routes import auth
    from app.trucks.routes import trucks
    from app.cargo.routes import cargo
    from app.main.routes import main

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(trucks, url_prefix="/trucks")
    app.register_blueprint(cargo, url_prefix="/cargo")
    app.register_blueprint(main)

    return app
