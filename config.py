import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_change_in_production'
    DEBUG = True
