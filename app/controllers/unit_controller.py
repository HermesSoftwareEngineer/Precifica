"""
Unit Controller - Handles unit management operations
"""

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from app import db
from app.models import Unit, User
from app.extensions import bcrypt
from app.utils.decorators import unit_required, unit_admin_required, admin_required
from app.utils.unit_helpers import get_user_active_unit, check_unit_admin_access
import logging

logger = logging.getLogger(__name__)

def create_unit():
    """Create a new unit."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name'):
        return jsonify({"error": "Unit name is required"}), 400
    
    try:
        # Create new unit
        unit = Unit(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            whatsapp=data.get('whatsapp'),
            address=data.get('address'),
            cnpj=data.get('cnpj'),
            logo_url=data.get('logo_url'),
            custom_fields=data.get('custom_fields', {})
        )
        
        # Add current user as admin
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        db.session.add(unit)
        db.session.flush()  # Get the unit ID and trigger event listeners
        
        # Check if user is already in unit (e.g., auto-added by super admin event listener)
        if not unit.users.filter_by(id=user.id).first():
            unit.users.append(user)
        
        # Set current user's active unit to this new unit
        user.active_unit_id = unit.id
        
        db.session.commit()
        
        return jsonify({
            "message": "Unit created successfully",
            "unit": unit.to_dict(include_users=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def get_unit(unit_id):
    """Get a single unit by ID."""
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    
    # Check if user has access to this unit
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user or not user.units.filter_by(id=unit_id).first():
        return jsonify({"error": "Access denied"}), 403
    
    return jsonify(unit.to_dict(include_users=True)), 200

def list_user_units():
    """List all units the current user belongs to."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    units = [unit.to_dict() for unit in user.units.all()]
    return jsonify({
        "units": units,
        "active_unit_id": user.active_unit_id
    }), 200

def update_unit(unit_id):
    """Update a unit (admin/manager only)."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    
    # Check if user is admin/manager of this unit
    if not check_unit_admin_access(unit_id):
        return jsonify({"error": "Admin/Manager access required"}), 403
    
    data = request.get_json()
    
    try:
        if 'name' in data:
            unit.name = data['name']
        if 'email' in data:
            unit.email = data['email']
        if 'phone' in data:
            unit.phone = data['phone']
        if 'whatsapp' in data:
            unit.whatsapp = data['whatsapp']
        if 'address' in data:
            unit.address = data['address']
        if 'cnpj' in data:
            unit.cnpj = data['cnpj']
        if 'logo_url' in data:
            unit.logo_url = data['logo_url']
        if 'custom_fields' in data:
            unit.custom_fields = data['custom_fields']
        
        db.session.commit()
        return jsonify({
            "message": "Unit updated successfully",
            "unit": unit.to_dict(include_users=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def set_active_unit(unit_id):
    """Set the active unit for the current user."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if user has access to this unit
    unit = user.units.filter_by(id=unit_id).first()
    if not unit:
        return jsonify({"error": "Access denied or unit not found"}), 403
    
    try:
        user.active_unit_id = unit_id
        db.session.commit()
        return jsonify({
            "message": "Active unit updated successfully",
            "active_unit_id": unit_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def add_user_to_unit(unit_id):
    """Add a user to a unit (admin/manager only)."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    
    # Check if current user is admin/manager of this unit
    if not check_unit_admin_access(unit_id):
        return jsonify({"error": "Admin/Manager access required"}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    role = data.get('role', 'member')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        unit.add_user(user, role)
        db.session.commit()
        return jsonify({
            "message": "User added to unit successfully",
            "unit": unit.to_dict(include_users=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def remove_user_from_unit(unit_id):
    """Remove a user from a unit (admin/manager only)."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    
    # Check if current user is admin/manager of this unit
    if not check_unit_admin_access(unit_id):
        return jsonify({"error": "Admin/Manager access required"}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Prevent removing global admins
    if user.is_admin:
        return jsonify({"error": "Cannot remove global admin from units"}), 403
    
    # Prevent removing the last admin
    if unit.get_user_role(user) == 'admin':
        admin_count = sum(1 for u in unit.users if unit.get_user_role(u) == 'admin')
        if admin_count <= 1:
            return jsonify({"error": "Cannot remove the last admin from the unit"}), 400
    
    try:
        unit.remove_user(user)
        db.session.commit()
        return jsonify({
            "message": "User removed from unit successfully",
            "unit": unit.to_dict(include_users=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def register_user_in_unit():
    """
    Register a new user and automatically add them to the current admin/manager's active unit.
    Only accessible by admins/managers of a unit.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'member')  # Default role is 'member'
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
    if not email:
        return jsonify({"error": "Email is required"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400
    
    # Validate role
    if role not in ['admin', 'manager', 'member']:
        return jsonify({"error": "Invalid role. Must be 'admin', 'manager', or 'member'"}), 400
    
    # Get current user
    user_id = get_jwt_identity()
    current_user = User.query.get(int(user_id))
    if not current_user or not current_user.active_unit_id:
        return jsonify({"error": "No active unit selected"}), 400
    
    unit = Unit.query.get(current_user.active_unit_id)
    if not unit:
        return jsonify({"error": "Active unit not found"}), 404
    
    # Get current user's role in the unit
    current_user_role = unit.get_user_role(current_user)
    
    # Managers can only create members and managers, not admins
    if current_user_role == 'manager' and role == 'admin':
        return jsonify({"error": "Managers cannot create admin users. Only admins can create other admins."}), 403
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400
    
    # Check if username already exists
    existing_username = User.query.filter_by(username=username).first()
    if existing_username:
        return jsonify({"error": "Username already taken"}), 400
    
    try:
        # Create new user
        logger.info(f"Admin/Manager {current_user.email} registering new user: {username} ({email}) in unit {unit.name}")
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.flush()  # Get the user ID
        
        # Add user to the unit with specified role
        unit.add_user(new_user, role=role)
        
        # Set the unit as active for the new user
        new_user.active_unit_id = unit.id
        
        db.session.commit()
        
        logger.info(f"User {new_user.email} (ID: {new_user.id}) registered and added to unit {unit.name} with role '{role}'")
        
        return jsonify({
            "message": f"User registered successfully and added to unit '{unit.name}'",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "role": role,
                "unit": unit.to_dict(),
                "active_unit_id": new_user.active_unit_id
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering user in unit: {e}")
        return jsonify({"error": str(e)}), 500

def update_user_in_unit(user_id_to_update):
    """
    Update a user in the current admin/manager's active unit.
    Only accessible by admins/managers of a unit.
    Cannot update passwords (use change-password endpoint instead).
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    # Get current user
    current_user_id = get_jwt_identity()
    current_user = User.query.get(int(current_user_id))
    if not current_user or not current_user.active_unit_id:
        return jsonify({"error": "No active unit selected"}), 400
    
    unit = Unit.query.get(current_user.active_unit_id)
    if not unit:
        return jsonify({"error": "Active unit not found"}), 404
    
    # Get user to update
    user_to_update = User.query.get(user_id_to_update)
    if not user_to_update:
        return jsonify({"error": "User not found"}), 404
    
    # Check if user to update is member of this unit
    if not unit.users.filter_by(id=user_id_to_update).first():
        return jsonify({"error": "User is not a member of this unit"}), 404
    
    # Get roles
    current_user_role = unit.get_user_role(current_user)
    target_user_role = unit.get_user_role(user_to_update)
    new_role = data.get('role', target_user_role)
    
    # Managers cannot edit admins
    if current_user_role == 'manager' and target_user_role == 'admin':
        return jsonify({"error": "Managers cannot edit admin users"}), 403
    
    # Managers cannot promote users to admin
    if current_user_role == 'manager' and new_role == 'admin':
        return jsonify({"error": "Managers cannot promote users to admin"}), 403
    
    # Validate new role
    if new_role and new_role not in ['admin', 'manager', 'member']:
        return jsonify({"error": "Invalid role. Must be 'admin', 'manager', or 'member'"}), 400
    
    # Prevent demotion of the last admin
    if target_user_role == 'admin' and new_role != 'admin':
        admin_count = sum(1 for u in unit.users if unit.get_user_role(u) == 'admin')
        if admin_count <= 1:
            return jsonify({"error": "Cannot demote the last admin of the unit"}), 400
    
    try:
        # Update username if provided
        if 'username' in data and data['username'] != user_to_update.username:
            # Check if new username is already taken
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != user_id_to_update:
                return jsonify({"error": "Username already taken"}), 400
            user_to_update.username = data['username']
        
        # Update email if provided
        if 'email' in data and data['email'] != user_to_update.email:
            # Check if new email is already taken
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id_to_update:
                return jsonify({"error": "Email already registered"}), 400
            user_to_update.email = data['email']
        
        # Update role if changed
        if new_role != target_user_role:
            # Remove and re-add with new role
            unit.remove_user(user_to_update)
            unit.add_user(user_to_update, role=new_role)
            logger.info(f"User {user_to_update.email} role changed from {target_user_role} to {new_role} in unit {unit.name}")
        
        db.session.commit()
        
        logger.info(f"User {user_to_update.email} (ID: {user_to_update.id}) updated in unit {unit.name}")
        
        return jsonify({
            "message": "User updated successfully",
            "user": {
                "id": user_to_update.id,
                "username": user_to_update.username,
                "email": user_to_update.email,
                "role": new_role,
                "unit": unit.to_dict()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user in unit: {e}")
        return jsonify({"error": str(e)}), 500

def delete_user_from_unit(user_id_to_delete):
    """
    Delete a user from the current admin/manager's active unit and delete the user account completely.
    Only accessible by admins/managers of a unit.
    """
    # Get current user
    current_user_id = get_jwt_identity()
    current_user = User.query.get(int(current_user_id))
    if not current_user or not current_user.active_unit_id:
        return jsonify({"error": "No active unit selected"}), 400
    
    unit = Unit.query.get(current_user.active_unit_id)
    if not unit:
        return jsonify({"error": "Active unit not found"}), 404
    
    # Get user to delete
    user_to_delete = User.query.get(user_id_to_delete)
    if not user_to_delete:
        return jsonify({"error": "User not found"}), 404
    
    # Check if user to delete is member of this unit
    if not unit.users.filter_by(id=user_id_to_delete).first():
        return jsonify({"error": "User is not a member of this unit"}), 404
    
    # Prevent deleting yourself
    if user_to_delete.id == current_user.id:
        return jsonify({"error": "Cannot delete yourself"}), 400
    
    # Get roles
    current_user_role = unit.get_user_role(current_user)
    target_user_role = unit.get_user_role(user_to_delete)
    
    # Managers cannot delete admins
    if current_user_role == 'manager' and target_user_role == 'admin':
        return jsonify({"error": "Managers cannot delete admin users"}), 403
    
    # Prevent deleting global admins
    if user_to_delete.is_admin:
        return jsonify({"error": "Cannot delete global admin users"}), 403
    
    # Prevent deleting the last admin
    if target_user_role == 'admin':
        admin_count = sum(1 for u in unit.users if unit.get_user_role(u) == 'admin')
        if admin_count <= 1:
            return jsonify({"error": "Cannot delete the last admin of the unit"}), 400
    
    try:
        # Remove user from ALL units first
        all_user_units = user_to_delete.units.all()
        for user_unit in all_user_units:
            user_unit.remove_user(user_to_delete)
        
        # Set user_id to NULL in conversations and evaluations (if the field allows NULL)
        # This preserves the data while removing the user reference
        from app.models.chat import Conversation
        from app.models.evaluation import Evaluation
        
        # Update conversations to remove user reference
        conversations = Conversation.query.filter_by(user_id=user_to_delete.id).all()
        for conv in conversations:
            conv.user_id = None
        
        # Note: Evaluations don't have user_id, they only have unit_id
        # So no need to update evaluations
        
        # Delete the user account completely
        db.session.delete(user_to_delete)
        db.session.commit()
        
        logger.info(f"User {user_to_delete.email} (ID: {user_to_delete.id}) deleted completely from system by {current_user.email}")
        
        return jsonify({
            "message": "User deleted successfully",
            "deleted_user_id": user_id_to_delete
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {e}")
        return jsonify({"error": str(e)}), 500

def upload_unit_logo(unit_id):
    """
    Upload a logo for a unit.
    Only accessible by admins/managers of the unit.
    """
    from flask import request
    from app.utils.file_upload import save_logo, delete_logo, get_logo_url
    
    # Get current user
    current_user_id = get_jwt_identity()
    current_user = User.query.get(int(current_user_id))
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Get unit
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    
    # Check if user has access to this unit
    if not current_user.units.filter_by(id=unit_id).first():
        return jsonify({"error": "Access denied"}), 403
    
    # Check if user is admin/manager of this unit
    user_role = unit.get_user_role(current_user)
    if user_role not in ['admin', 'manager']:
        return jsonify({"error": "Admin/Manager access required"}), 403
    
    # Check if file is in request
    if 'logo' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['logo']
    
    try:
        # Delete old logo if exists
        if unit.logo_url:
            # Extract filename from URL if it's a local file
            if unit.logo_url.startswith('/api/uploads/'):
                old_filename = unit.logo_url.split('/')[-1]
                delete_logo(old_filename)
        
        # Save new logo
        success, result = save_logo(file, unit_id)
        
        if not success:
            return jsonify({"error": result}), 400
        
        # Update unit with new logo URL
        unit.logo_url = get_logo_url(result)
        db.session.commit()
        
        logger.info(f"Logo uploaded for unit {unit.name} (ID: {unit_id})")
        
        return jsonify({
            "message": "Logo uploaded successfully",
            "logo_url": unit.logo_url
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading logo: {e}")
        return jsonify({"error": str(e)}), 500

def delete_unit_logo(unit_id):
    """
    Delete the logo of a unit.
    Only accessible by admins/managers of the unit.
    """
    from app.utils.file_upload import delete_logo
    
    # Get current user
    current_user_id = get_jwt_identity()
    current_user = User.query.get(int(current_user_id))
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Get unit
    unit = Unit.query.get(unit_id)
    if not unit:
        return jsonify({"error": "Unit not found"}), 404
    
    # Check if user has access to this unit
    if not current_user.units.filter_by(id=unit_id).first():
        return jsonify({"error": "Access denied"}), 403
    
    # Check if user is admin/manager of this unit
    user_role = unit.get_user_role(current_user)
    if user_role not in ['admin', 'manager']:
        return jsonify({"error": "Admin/Manager access required"}), 403
    
    try:
        # Delete logo file if it's a local file
        if unit.logo_url and unit.logo_url.startswith('/api/uploads/'):
            filename = unit.logo_url.split('/')[-1]
            delete_logo(filename)
        
        # Clear logo_url in database
        unit.logo_url = None
        db.session.commit()
        
        logger.info(f"Logo deleted for unit {unit.name} (ID: {unit_id})")
        
        return jsonify({
            "message": "Logo deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting logo: {e}")
        return jsonify({"error": str(e)}), 500
