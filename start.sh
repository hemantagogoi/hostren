#!/bin/bash

# Render startup script for Question Paper App
echo "🚀 Starting Question Paper App deployment..."

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:/app"

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
        print('❌ DATABASE_URL not found')
        return False
    
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
                password=parsed.password
            )
            conn.close()
            print('✅ Database connection successful')
            return True
        except Exception as e:
            print(f'⏳ Waiting for database... (attempt {retry_count + 1}/{max_retries})')
            time.sleep(2)
            retry_count += 1
    
    print('❌ Database connection failed')
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
                print('⚠️ Approval columns missing - run migration manually')
        except Exception as e:
            print('⚠️ Could not verify approval columns:', str(e))
            
    except Exception as e:
        print('❌ Error initializing database:', str(e))
        exit(1)
"

echo "🎉 Application ready to start!"
exec gunicorn app:app --config gunicorn_config.py
