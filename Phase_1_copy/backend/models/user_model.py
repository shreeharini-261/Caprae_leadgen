from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models.lead_model import db
from datetime import datetime

class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='user', nullable=False)
    subscription_tier = db.Column(db.String(20), default='free', nullable=False)  # free, bronze, silver, gold
    
    @staticmethod
    def create_default_user():
        """Create default user with free tier"""
        user = User.query.filter_by(username='user').first()
        if user:
            user.subscription_tier = 'free'
            db.session.commit()
    company = db.Column(db.String(100))  # New field for company
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches"""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role

    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'

    def is_developer(self):
        """Check if user is developer"""
        return self.role == 'developer'

    def is_staff(self):
        """Check if user is admin or developer"""
        return self.role in ['admin', 'developer']

    def __repr__(self):
        return f'<User {self.username}>' 