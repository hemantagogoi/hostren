import os


class Config:
    DEBUG = False
    TESTING = False
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get("EMAIL_SERVER")
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("EMAIL_USER")
    MAIL_PASSWORD = os.environ.get("EMAIL_PASS")
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300


class DevelopmentConfig(Config):
    SECRET_KEY = "166839997171300f4a1f899733c043e20d1758d3595ff0c8"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/flaskapp")
    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    SECRET_KEY = "166839997171300f4a1f899733c043e20d1758d3595ff0c8"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/flaskapp_test")
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = False
    ENV = "production"
    
    def __init__(self):
        super().__init__()
        # Require PostgreSQL for production - no SQLite fallback
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required for production")
        self.SQLALCHEMY_DATABASE_URI = database_url
