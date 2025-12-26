from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.controllers.auth_controller import register_user, login_user_by_email, logout, change_user_password
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

@auth_bp.route("/change-password", methods=['POST'])
@jwt_required()
def change_password():
    logger.info("Change password route accessed")
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'error': 'Missing current or new password'}), 400
        
    success, message = change_user_password(current_user_id, data['current_password'], data['new_password'])
    
    if success:
        return jsonify({'message': message}), 200
    else:
        # If it's an invalid password, 401 might be more appropriate, but 400 is also fine for bad request logic.
        # Given the controller returns "Invalid current password", 400 or 401 is fine. Let's stick to 400 for simplicity or 401 if strictly auth failure.
        # Usually "Invalid current password" implies the request is bad because the provided credentials to perform the action are wrong.
        return jsonify({'error': message}), 400

@auth_bp.route("/logout", methods=['POST'])
def logout_route():
    logger.info("Logout route accessed")
    logout()
    return jsonify({'message': 'Logged out successfully'}), 200
