from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.controllers.conversation_controller import (
    create_conversation, get_user_conversations, get_conversation_by_id,
    update_conversation_title, delete_conversation_by_id, get_conversation_messages
)

conversation_bp = Blueprint('conversation', __name__, url_prefix='/api/conversations')

@conversation_bp.route('/', methods=['GET'])
@login_required
def list_conversations():
    conversations = get_user_conversations()
    return jsonify([c.to_dict() for c in conversations]), 200

@conversation_bp.route('/', methods=['POST'])
@login_required
def new_conversation():
    data = request.get_json() or {}
    title = data.get('title', 'New Conversation')
    conversation = create_conversation(title)
    return jsonify(conversation.to_dict()), 201

@conversation_bp.route('/<int:conversation_id>', methods=['GET'])
@login_required
def get_conversation(conversation_id):
    conversation = get_conversation_by_id(conversation_id)
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    if conversation.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    messages = get_conversation_messages(conversation_id)
    
    response = conversation.to_dict()
    response['messages'] = [m.to_dict() for m in messages]
    return jsonify(response), 200

@conversation_bp.route('/<int:conversation_id>', methods=['PUT'])
@login_required
def update_conversation(conversation_id):
    conversation = get_conversation_by_id(conversation_id)
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
        
    if conversation.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    updated_conversation = update_conversation_title(conversation_id, title)
    return jsonify(updated_conversation.to_dict()), 200

@conversation_bp.route('/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    conversation = get_conversation_by_id(conversation_id)
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
        
    if conversation.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    if delete_conversation_by_id(conversation_id):
        return jsonify({'message': 'Conversation deleted'}), 200
    else:
        return jsonify({'error': 'Failed to delete conversation'}), 500
