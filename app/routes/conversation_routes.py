from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.controllers.conversation_controller import (
    create_conversation, get_user_conversations, get_conversation_by_id,
    update_conversation_title, delete_conversation_by_id, get_conversation_messages
)
import logging

logger = logging.getLogger(__name__)

conversation_bp = Blueprint('conversation', __name__, url_prefix='/api/conversations')

@conversation_bp.route('/', methods=['GET'])
@jwt_required()
def list_conversations():
    user_id = get_jwt_identity()
    logger.info(f"User {user_id} listing conversations")
    conversations = get_user_conversations()
    return jsonify([c.to_dict() for c in conversations]), 200

@conversation_bp.route('/', methods=['POST'])
@jwt_required()
def new_conversation():
    user_id = get_jwt_identity()
    logger.info(f"User {user_id} creating new conversation")
    data = request.get_json() or {}
    
    title = data.get('title')
    if not title:
        message = data.get('message')
        if message:
            from app.controllers.bot_controller import generate_conversation_title
            title = generate_conversation_title(message)
        else:
            title = 'New Conversation'

    conversation = create_conversation(title)
    return jsonify(conversation.to_dict()), 201

@conversation_bp.route('/<int:conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    user_id = int(get_jwt_identity())
    logger.info(f"User {user_id} requesting conversation {conversation_id}")
    conversation = get_conversation_by_id(conversation_id)
    if not conversation:
        logger.warning(f"Conversation {conversation_id} not found")
        return jsonify({'error': 'Conversation not found'}), 404
    
    from app.models.user import User
    user = User.query.get(user_id)
    if conversation.user_id != user_id and not user.is_admin:
        logger.warning(f"User {user_id} unauthorized to access conversation {conversation_id}")
        return jsonify({'error': 'Unauthorized'}), 403

    messages = get_conversation_messages(conversation_id)
    
    response = conversation.to_dict()
    response['messages'] = [m.to_dict() for m in messages]
    return jsonify(response), 200

@conversation_bp.route('/<int:conversation_id>', methods=['PUT'])
@jwt_required()
def update_conversation(conversation_id):
    user_id = int(get_jwt_identity())
    logger.info(f"User {user_id} updating conversation {conversation_id}")
    conversation = get_conversation_by_id(conversation_id)
    if not conversation:
        logger.warning(f"Conversation {conversation_id} not found")
        return jsonify({'error': 'Conversation not found'}), 404
    
    from app.models.user import User
    user = User.query.get(user_id)
    if conversation.user_id != user_id and not user.is_admin:
        logger.warning(f"User {user_id} unauthorized to update conversation {conversation_id}")
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    title = data.get('title')
    if not title:
        logger.warning("Title is required for update")
        return jsonify({'error': 'Title is required'}), 400

    updated_conversation = update_conversation_title(conversation_id, title)
    return jsonify(updated_conversation.to_dict()), 200

@conversation_bp.route('/<int:conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conversation_id):
    user_id = int(get_jwt_identity())
    logger.info(f"User {user_id} deleting conversation {conversation_id}")
    conversation = get_conversation_by_id(conversation_id)
    if not conversation:
        logger.warning(f"Conversation {conversation_id} not found")
        return jsonify({'error': 'Conversation not found'}), 404
    
    from app.models.user import User
    user = User.query.get(user_id)
    if conversation.user_id != user_id and not user.is_admin:
        logger.warning(f"User {user_id} unauthorized to delete conversation {conversation_id}")
        return jsonify({'error': 'Unauthorized'}), 403

    if delete_conversation_by_id(conversation_id):
        logger.info(f"Conversation {conversation_id} deleted successfully")
        return jsonify({'message': 'Conversation deleted'}), 200
    else:
        logger.error(f"Failed to delete conversation {conversation_id}")
        return jsonify({'error': 'Failed to delete conversation'}), 500
