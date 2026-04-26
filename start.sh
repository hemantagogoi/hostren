#!/bin/bash

# Railway startup script for Question Paper App
echo "🚀 Starting Question Paper App on Railway..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:/app"

# Check if we're on Railway
if [ -n "$RAILWAY_ENVIRONMENT" ] || [ -n "$RAILWAY_SERVICE_NAME" ]; then
    echo "🚂 Detected Railway environment"
    export FLASK_ENV="production"
    export RAILWAY_ENVIRONMENT="production"
fi

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python -c "
import time
import psycopg2
import os
from urllib.parse import urlparse

def wait_for_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print('❌ DATABASE_URL not found in environment variables')
        print('Available env vars:', [k for k in os.environ.keys() if 'DB' in k.upper() or 'DATABASE' in k.upper()])
        return False
    
    print(f'📡 Database URL found: {db_url.split(\"@\")[1] if \"@\" in db_url else \"URL found\"}')
    
    parsed = urlparse(db_url)
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading /
                user=parsed.username,
                password=parsed.password,
                connect_timeout=5
            )
            conn.close()
            print('✅ Database connection successful')
            return True
        except Exception as e:
            print(f'⏳ Waiting for database... (attempt {retry_count + 1}/{max_retries}) - {str(e)[:50]}')
            time.sleep(2)
            retry_count += 1
    
    print('❌ Database connection failed after all retries')
    return False

wait_for_db()
"

# Initialize database
echo "🔧 Initializing database..."
python -c "
from app import app
with app.app_context():
    from flaskapp import db
    try:
        print('Creating database tables...')
        db.create_all()
        print('✅ Database tables created successfully')
        
        # Check if we need to run approval migration
        from flaskapp.models import User
        try:
            # Test if approval columns exist
            user = User.query.first()
            if hasattr(user, 'is_approved'):
                print('✅ Approval columns already exist')
            else:
                print('⚠️ Approval columns missing - running migration...')
                # Run approval migration
                import psycopg2
                from urllib.parse import urlparse
                db_url = os.environ.get('DATABASE_URL')
                if db_url:
                    parsed = urlparse(db_url)
                    conn = psycopg2.connect(
                        host=parsed.hostname,
                        port=parsed.port or 5432,
                        database=parsed.path[1:],
                        user=parsed.username,
                        password=parsed.password
                    )
                    cursor = conn.cursor()
                    
                    # Add approval columns
                    cursor.execute('ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT FALSE NOT NULL')
                    cursor.execute('ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS approval_requested_at TIMESTAMP')
                    cursor.execute('ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP')
                    cursor.execute('ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS approved_by INTEGER')
                    
                    # Update existing users
                    cursor.execute('UPDATE \"user\" SET is_approved = TRUE, approval_requested_at = NOW(), approved_at = NOW() WHERE is_approved = FALSE OR is_approved IS NULL')
                    
                    conn.commit()
                    cursor.close()
                    conn.close()
                    print('✅ Approval migration completed')
        except Exception as e:
            print('⚠️ Could not verify approval columns:', str(e))
            
    except Exception as e:
        print('❌ Error initializing database:', str(e))
        print('⚠️ Continuing startup despite database error...')
        # Don't exit(1) - let the app start and handle DB errors gracefully
"

echo "🎉 Application ready to start!"
exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 3 --timeout 120
