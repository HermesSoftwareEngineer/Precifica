"""
Helper functions for unit-related operations.
"""

from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User
import logging

logger = logging.getLogger(__name__)

def get_user_with_active_unit():
    """
    Retorna o usuário autenticado e valida se ele tem uma unidade ativa selecionada
    E se ele é realmente MEMBRO dessa unidade.
    
    Returns:
        tuple: (user, None) se sucesso, ou (None, error_response) se falha
    """
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            logger.warning(f"User {user_id} not found")
            return None, (jsonify({'error': 'User not found'}), 404)
        
        if not user.active_unit_id:
            logger.warning(f"User {user_id} has no active unit selected")
            return None, (jsonify({'error': 'No active unit selected. Please select a unit first.'}), 400)
        
        # Verifica se o usuário é membro da unidade ativa
        is_member = user.units.filter_by(id=user.active_unit_id).first() is not None
        if not is_member:
            logger.warning(f"User {user_id} is not a member of unit {user.active_unit_id}")
            return None, (jsonify({'error': 'You are not a member of the selected unit. Access denied.'}), 403)
        
        return user, None
    
    except Exception as e:
        logger.error(f"Error getting user with active unit: {e}")
        return None, (jsonify({'error': 'Authentication error'}), 401)

def get_user_active_unit():
    """Get the active unit of the current authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return None
    return user.active_unit

def get_user_units():
    """Get all units the current authenticated user belongs to."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return []
    return user.units.all()

def check_unit_access(unit_id, user=None):
    """
    Check if a user has access to a specific unit.
    If user is None, uses the current authenticated user.
    """
    if user is None:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return False
    
    return user.units.filter_by(id=unit_id).first() is not None

def check_unit_admin_access(unit_id, user=None):
    """
    Check if a user is admin/manager of a specific unit.
    If user is None, uses the current authenticated user.
    """
    if user is None:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return False
    
    unit = user.units.filter_by(id=unit_id).first()
    if not unit:
        return False
    
    role = unit.get_user_role(user)
    return role in ['admin', 'manager']
