"""
Unit Routes - API endpoints for unit management
"""

from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.controllers import unit_controller
from app.utils.decorators import unit_admin_required

unit_bp = Blueprint('unit', __name__, url_prefix='/api/units')

# Unit CRUD operations
@unit_bp.route('', methods=['POST'])
@jwt_required()
def create_unit():
    return unit_controller.create_unit()

@unit_bp.route('/<int:unit_id>', methods=['GET'])
@jwt_required()
def get_unit(unit_id):
    return unit_controller.get_unit(unit_id)

@unit_bp.route('', methods=['GET'])
@jwt_required()
def list_units():
    return unit_controller.list_user_units()

@unit_bp.route('/<int:unit_id>', methods=['PUT'])
@jwt_required()
def update_unit(unit_id):
    return unit_controller.update_unit(unit_id)

# Unit selection
@unit_bp.route('/<int:unit_id>/set-active', methods=['POST'])
@jwt_required()
def set_active_unit(unit_id):
    return unit_controller.set_active_unit(unit_id)

# User management within unit
@unit_bp.route('/<int:unit_id>/users', methods=['POST'])
@jwt_required()
def add_user_to_unit(unit_id):
    return unit_controller.add_user_to_unit(unit_id)

@unit_bp.route('/<int:unit_id>/users', methods=['DELETE'])
@jwt_required()
def remove_user_from_unit(unit_id):
    return unit_controller.remove_user_from_unit(unit_id)

# User registration within unit (admin/manager only)
@unit_bp.route('/register-user', methods=['POST'])
@jwt_required()
@unit_admin_required
def register_user_in_unit():
    """
    Register a new user and add them to the current admin/manager's active unit.
    Only accessible by admins/managers.
    """
    return unit_controller.register_user_in_unit()

# User management: edit and delete (admin/manager only)
@unit_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@unit_admin_required
def update_user_in_unit(user_id):
    """
    Update a user in the current admin/manager's active unit.
    Only accessible by admins/managers.
    """
    return unit_controller.update_user_in_unit(user_id)

@unit_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@unit_admin_required
def delete_user_from_unit(user_id):
    """
    Delete a user from the current admin/manager's active unit.
    Only accessible by admins/managers.
    """
    return unit_controller.delete_user_from_unit(user_id)

# Logo management (admin/manager only)
@unit_bp.route('/<int:unit_id>/logo', methods=['POST'])
@jwt_required()
def upload_unit_logo_route(unit_id):
    """
    Upload a logo for a unit.
    Only accessible by admins/managers of the unit.
    """
    return unit_controller.upload_unit_logo(unit_id)

@unit_bp.route('/<int:unit_id>/logo', methods=['DELETE'])
@jwt_required()
def delete_unit_logo_route(unit_id):
    """
    Delete the logo of a unit.
    Only accessible by admins/managers of the unit.
    """
    return unit_controller.delete_unit_logo(unit_id)
