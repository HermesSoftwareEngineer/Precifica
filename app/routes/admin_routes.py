from flask import Blueprint, request, jsonify
from app.controllers.admin_controller import get_all_users, get_user_by_id, create_user_admin, update_user_admin, delete_user_admin
from app.utils.decorators import admin_required
from flask_login import login_required
from app.models.user import User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/users", methods=['GET'])
@login_required
@admin_required
def users_list():
    users = get_all_users()
    return jsonify([user.to_dict() for user in users]), 200

@admin_bp.route("/users", methods=['POST'])
@login_required
@admin_required
def new_user():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already taken'}), 400

    is_admin = data.get('is_admin', False)
    user = create_user_admin(data['username'], data['email'], data['password'], is_admin)
    return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201

@admin_bp.route("/users/<int:user_id>", methods=['PUT'])
@login_required
@admin_required
def edit_user(user_id):
    user = get_user_by_id(user_id)
    data = request.get_json()
    
    username = data.get('username', user.username)
    email = data.get('email', user.email)
    is_admin = data.get('is_admin', user.is_admin)

    if username != user.username and User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400
    if email != user.email and User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already taken'}), 400

    updated_user = update_user_admin(user, username, email, is_admin)
    return jsonify({'message': 'User updated successfully', 'user': updated_user.to_dict()}), 200

@admin_bp.route("/users/<int:user_id>", methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = get_user_by_id(user_id)
    delete_user_admin(user)
    return jsonify({'message': 'User deleted successfully'}), 200
