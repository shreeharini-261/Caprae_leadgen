from models.user_model import User, db
from flask_login import login_user, logout_user

class AuthController:
    @staticmethod
    def register(username, email, password, role='user', company=''):
        """Register a new user"""
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return False, "Username already exists"

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return False, "Email already registered"

        # Validate role
        valid_roles = ['admin', 'developer', 'user']
        if role not in valid_roles:
            return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"

        try:
            # Create new user
            user = User(username=username, email=email, role=role, company=company)
            user.set_password(password)
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            return True, "Registration successful"
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed: {str(e)}"

    @staticmethod
    def login(username, password):
        """Login a user"""
        try:
            # Find user by username
            user = User.query.filter_by(username=username).first()
            
            # Check if user exists and password is correct
            if user and user.check_password(password):
                login_user(user)
                return True, "Login successful"
            
            return False, "Invalid username or password"
        except Exception as e:
            return False, f"Login failed: {str(e)}"

    @staticmethod
    def logout():
        """Logout current user"""
        try:
            logout_user()
            return True, "Logout successful"
        except Exception as e:
            return False, f"Logout failed: {str(e)}" 