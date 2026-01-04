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