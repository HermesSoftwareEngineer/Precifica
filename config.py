import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_change_in_production'
    # Ensure DATABASE_URL is set in .env for Supabase connection
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URL set for Flask application")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
