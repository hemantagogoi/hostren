"""
Create admin user for the application.
Usage: python create_admin.py <email> <password> [username]
"""

import os
import sys

# Add the parent directory to the path to import flaskapp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flaskapp import create_app, db, bcrypt
from flaskapp.models import Admin

def create_admin_user(email, password, username="admin"):
    """Create admin user"""
    from flaskapp.config import DevelopmentConfig
    app = create_app(config_class=DevelopmentConfig)
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = Admin.query.filter_by(email=email).first()
        
        if existing_admin:
            print(f"Admin user with email {email} already exists. Updating password...")
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            existing_admin.password = hashed_password
            existing_admin.username = username
            db.session.commit()
            print("Admin password updated successfully!")
        else:
            # Check if username already exists
            existing_username = Admin.query.filter_by(username=username).first()
            if existing_username:
                print(f"Username {username} already exists. Please choose a different username.")
                return
            
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            admin = Admin(
                username=username,
                email=email,
                password=hashed_password
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created successfully!")
            print(f"Email: {email}")
            print(f"Username: {username}")
            print(f"Password: {password}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_admin.py <email> <password> [username]")
        print("Example: python create_admin.py admin@qpg.com admin123")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    username = sys.argv[3] if len(sys.argv) > 3 else "admin"
    
    if len(password) < 6:
        print("Password must be at least 6 characters long.")
        sys.exit(1)
    
    create_admin_user(email, password, username)
