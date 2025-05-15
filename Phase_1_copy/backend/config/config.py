import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base config class"""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    STRIPE_PUBLIC_KEY = 'pk_test_51RNp9cFS9KhotLbMiJM95rAjhuxjTwgjPpRLObOd1ghpwZHwZHOLDIVuxbp4wfXCJBHSLtZhoL99CdaTpOpWAY1L00GcymT5Xj'
    STRIPE_SECRET_KEY = 'sk_test_51RNp9cFS9KhotLbM7Qfe3wOjhR0gWezVAbsFhmrxpRibj8QqtVBqvXWFNagq1uz5luTEuIi5nxdcOIkMaz6xHLrt00MUplXF0x'
    STRIPE_PRICES = {
        'bronze': 'price_1ROgvdFS9KhotLbMuOGezRqB',
        'silver': 'price_1ROgv1FS9KhotLbMCvpnsehu',
        'gold': 'price_1ROgtyFS9KhotLbMMuhSgaS7'
    }
    STRIPE_WEBHOOK_SECRET = 'whsec_rzeSuH4PbfYqi84rwmgFZACS5q4y8Jhf'  

class DevelopmentConfig(Config):
    """Development config"""
    DEBUG = True

class ProductionConfig(Config):
    """Production config"""
    DEBUG = False

# Use development config by default
config = DevelopmentConfig