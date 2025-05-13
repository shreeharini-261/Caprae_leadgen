import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base config class"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class DevelopmentConfig(Config):
    """Development config"""
    DEBUG = True

class ProductionConfig(Config):
    """Production config"""
    DEBUG = False

# Use development config by default
config = DevelopmentConfig 