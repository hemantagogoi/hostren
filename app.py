try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    sentry_sdk.init(
        dsn="https://1fdf413ccfcc4a249f79519bfc269965@o374456.ingest.sentry.io/5192531",
        integrations=[FlaskIntegration()],
    )
except ImportError:
    pass

from flaskapp import create_app

from flaskapp.config import DevelopmentConfig, ProductionConfig

import os

# Use production config in production environment, development config otherwise
if os.environ.get("RENDER"):
    app = create_app(config_class=ProductionConfig)
else:
    app = create_app(config_class=DevelopmentConfig)

# Initialize database tables
with app.app_context():
    from flaskapp import db
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")


@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        from flaskapp import db
        # Test database connection
        db.session.execute('SELECT 1')
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}, 500


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers["X-UA-Compatible"] = "IE=Edge,chrome=1"
    response.headers["Cache-Control"] = "must-revalidate, max-age=0"
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
