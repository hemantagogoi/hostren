"""
Initialize admin user for the application.
Run this script to create or update the admin account.
"""

import os
import sys

# Add the parent directory to the path to import flaskapp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flaskapp import create_app, db, bcrypt
from flaskapp.models import Admin

def create_admin_user(email, password, username="admin"):
    """Create or update admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = Admin.query.filter_by(email=email).first()
        
        if existing_admin:
            print(f"Admin user with email {email} already exists.")
            choice = input("Do you want to update the password? (y/n): ")
            if choice.lower() == 'y':
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                existing_admin.password = hashed_password
                existing_admin.username = username
                db.session.commit()
                print("Admin password updated successfully!")
            else:
                print("No changes made.")
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
    print("=== Admin User Setup ===")
    
    # Get admin credentials
    email = input("Enter admin email: ").strip()
    if not email:
        email = "admin@qpg.com"
        print(f"Using default email: {email}")
    
    username = input("Enter admin username: ").strip()
    if not username:
        username = "admin"
        print(f"Using default username: {username}")
    
    password = input("Enter admin password: ").strip()
    if not password:
        password = "admin123"
        print(f"Using default password: {password}")
    
    if len(password) < 6:
        print("Password must be at least 6 characters long.")
        sys.exit(1)
    
    create_admin_user(email, password, username)
