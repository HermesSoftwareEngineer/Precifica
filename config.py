import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_change_in_production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt_secret_key_change_in_production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    # Ensure DATABASE_URL is set in .env for Supabase connection
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URL set for Flask application")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    FRONTEND_URL = os.environ.get('FRONTEND_URL')
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    UNIT_LOGO_FOLDER = os.path.join(UPLOAD_FOLDER, 'unit_logos')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    ALLOWED_LOGO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
