import os
import logging

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_login import LoginManager
from flask_mail import Mail
from flask_minify import minify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.exc import OperationalError

from flaskapp.config import Config

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "users.login"
login_manager.login_message_category = "info"
mail = Mail()
cache = Cache()
APP_PATH = os.path.dirname(os.path.abspath(__file__))


def create_app(config_class=Config):
    """To create

    Keyword Arguments:
        config_class {object} -- It configures app (default: {Config})

    Returns:
        App -- it creates app using configuration from config_class
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database with error handling
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Test database connection
    with app.app_context():
        try:
            db.engine.connect()
            app.logger.info("Database connection successful")
        except OperationalError as e:
            app.logger.warning(f"Database connection failed: {e}")
            app.logger.warning("App will start without database connection")

    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    minify(app=app, html=True, js=True, cssless=True)

    from flaskapp.blueprints.admin.routes import admin
    from flaskapp.blueprints.paper_gen.routes import paper_gen
    from flaskapp.blueprints.users.routes import users
    from flaskapp.blueprints.main.routes import main
    from flaskapp.blueprints.errors.routes import errors

    app.register_blueprint(admin)
    app.register_blueprint(paper_gen)
    app.register_blueprint(users)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    return app
