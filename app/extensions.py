from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from contextvars import ContextVar
from typing import Optional

db = SQLAlchemy()

# Context variable used to pass the authenticated user_id to bot tools
# that run outside of a Flask request context (background threads, etc.)
bot_user_id_var: ContextVar[Optional[int]] = ContextVar('bot_user_id', default=None)
bcrypt = Bcrypt()
login_manager = LoginManager()
cors = CORS()
jwt = JWTManager()
# login_manager.login_view = 'auth.login' # Removed for API
# login_manager.login_message_category = 'info'

@login_manager.unauthorized_handler
def unauthorized():
    from flask import jsonify
    return jsonify({'error': 'Unauthorized', 'message': 'Please log in to access this resource'}), 401
