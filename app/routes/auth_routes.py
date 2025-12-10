from flask import Blueprint, request, jsonify
from app.controllers.auth_controller import register_user, login_user_by_email, logout
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=['POST'])
def register():
    logger.info("Register route accessed")
    
    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        logger.warning("Missing required fields for registration")
        return jsonify({'error': 'Missing required fields'}), 400
        
    if User.query.filter_by(username=data['username']).first():
        logger.warning(f"Username already taken: {data['username']}")
        return jsonify({'error': 'Username already taken'}), 400
    if User.query.filter_by(email=data['email']).first():
        logger.warning(f"Email already taken: {data['email']}")
        return jsonify({'error': 'Email already taken'}), 400

    user = register_user(data['username'], data['email'], data['password'])
    logger.info(f"User registered via route: {user.id}")
    return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201

@auth_bp.route("/login", methods=['POST'])
def login():
    logger.info("Login route accessed")
        
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        logger.warning("Missing email or password for login")
        return jsonify({'error': 'Missing email or password'}), 400

    access_token, user = login_user_by_email(data['email'], data['password'])
    if access_token:
        logger.info(f"User logged in via route: {user.id}")
        return jsonify({
            'message': 'Login successful', 
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
    else:
        logger.warning(f"Login failed for email: {data.get('email')}")
        return jsonify({'error': 'Login Unsuccessful. Please check email and password'}), 401

@auth_bp.route("/logout", methods=['POST'])
def logout_route():
    logger.info("Logout route accessed")
    logout()
    return jsonify({'message': 'Logged out successfully'}), 200
