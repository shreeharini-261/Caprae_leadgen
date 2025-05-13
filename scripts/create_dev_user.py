from flask import Flask
import sys
import os

# Add parent directory to path to run script independently
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.user_model import User, db

def create_users():
    """Create development and admin users"""
    app = create_app()
    with app.app_context():
        # Create developer user
        dev_user = User.query.filter_by(username='developer').first()
        if not dev_user:
            dev_user = User(
                username='developer',
                email='developer@example.com',
                role='developer'
            )
            dev_user.set_password('developer123')
            db.session.add(dev_user)
            print("Developer user created successfully!")
            print("Username: developer")
            print("Password: developer123")
        else:
            print("Developer user already exists!")

        # Create admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("Admin user already exists!")

        # Create regular user
        user = User.query.filter_by(username='user').first()
        if not user:
            user = User(username='user', email='user@example.com', role='user', subscription_tier='free')
            user.set_password('user123')
            db.session.add(user)
            print("Regular user created successfully!")
            print("Username: user")
            print("Password: user123")
        else:
            print("Regular user already exists!")

        db.session.commit()

if __name__ == '__main__':
    create_users()