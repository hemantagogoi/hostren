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
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    DEBUG = True
    ENV = "development"


class RailwayConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY", "railway-secret-key")
    DEBUG = False
    ENV = "production"
    
    def __init__(self):
        super().__init__()
        # Railway provides DATABASE_URL environment variable
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            # Convert postgres:// to postgresql:// for SQLAlchemy
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            self.SQLALCHEMY_DATABASE_URI = database_url
        # If no DATABASE_URL, keep the default from parent class (None)


class TestingConfig(Config):
    SECRET_KEY = "166839997171300f4a1f899733c043e20d1758d3595ff0c8"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = False
    ENV = "production"
    
    def __init__(self):
        super().__init__()
        # Use DATABASE_URL from environment
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            self.SQLALCHEMY_DATABASE_URI = database_url
        # If no DATABASE_URL, keep the default from parent class (None)


class SupabaseConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY", "supabase-secret-key")
    DEBUG = False
    ENV = "production"
    
    def __init__(self):
        super().__init__()
        # Supabase provides DATABASE_URL environment variable
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            # Convert postgres:// to postgresql:// for SQLAlchemy
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            self.SQLALCHEMY_DATABASE_URI = database_url
        # If no DATABASE_URL, keep the default from parent class (None)
        
        # Supabase specific settings
        self.SUPABASE_URL = os.environ.get("SUPABASE_URL")
        self.SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
        self.SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
