from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user or not user.is_admin:
            return jsonify({"error": "Admins only!"}), 403
        return f(*args, **kwargs)
    return decorated_function

def unit_required(f):
    """Decorator to ensure user has an active unit selected."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404
        if not user.active_unit_id:
            return jsonify({"error": "No active unit selected. Please select a unit first."}), 400
        return f(*args, **kwargs)
    return decorated_function

def unit_admin_required(f):
    """Decorator to ensure user is admin/manager of their active unit."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404
        if not user.active_unit_id:
            return jsonify({"error": "No active unit selected"}), 400
        if not user.active_unit or user.active_unit.get_user_role(user) not in ['admin', 'manager']:
            return jsonify({"error": "Admin/Manager access required for this unit"}), 403
        return f(*args, **kwargs)
    return decorated_function
