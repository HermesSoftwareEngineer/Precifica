from app.extensions import db
from app.models.chat import Conversation, Message
from app.models.user import User
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
import logging

logger = logging.getLogger(__name__)

def create_conversation(title="New Conversation"):
    try:
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.active_unit_id:
            logger.error("User has no active unit")
            return None
        unit_id = user.active_unit_id
    except:
        user_id = None
        unit_id = None
        logger.warning("Creating conversation without authentication")
    
    logger.info(f"Creating conversation: title='{title}', user_id={user_id}, unit_id={unit_id}")
    conversation = Conversation(user_id=user_id, unit_id=unit_id, title=title)
    db.session.add(conversation)
    db.session.commit()
    logger.info(f"Conversation created: {conversation.id}")
    return conversation

def get_user_conversations():
    try:
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.active_unit_id:
            logger.warning("User has no active unit")
            return []
    except:
        logger.warning("Unauthenticated user attempted to fetch conversations")
        return []
    
    logger.info(f"Fetching conversations for user: {user_id}, unit: {user.active_unit_id}")
    return Conversation.query.filter_by(
        user_id=user_id,
        unit_id=user.active_unit_id
    ).filter(Conversation.evaluation_id.is_(None)).order_by(Conversation.updated_at.desc()).all()

def get_conversation_by_id(conversation_id):
    logger.info(f"Fetching conversation: {conversation_id}")
    
    try:
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.active_unit_id:
            logger.warning("User has no active unit")
            return None
        
        conversation = Conversation.query.get(conversation_id)
        
        # Check if conversation belongs to user's active unit
        if conversation and conversation.unit_id != user.active_unit_id:
            logger.warning(f"Access denied to conversation {conversation_id}")
            return None
        
        return conversation
    except:
        return Conversation.query.get(conversation_id)

def update_conversation_title(conversation_id, new_title):
    logger.info(f"Updating title for conversation {conversation_id} to '{new_title}'")
    
    try:
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.active_unit_id:
            logger.warning("User has no active unit")
            return None
    except:
        pass
    
    conversation = Conversation.query.get(conversation_id)
    if conversation:
        # Check if conversation belongs to user's active unit (if authenticated)
        if user and conversation.unit_id != user.active_unit_id:
            logger.warning(f"Access denied to conversation {conversation_id}")
            return None
        
        conversation.title = new_title
        db.session.commit()
        logger.info(f"Conversation {conversation_id} title updated")
    else:
        logger.warning(f"Conversation {conversation_id} not found for update")
    return conversation

def delete_conversation_by_id(conversation_id):
    logger.info(f"Deleting conversation: {conversation_id}")
    
    try:
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.active_unit_id:
            logger.warning("User has no active unit")
            return False
    except:
        pass
    
    conversation = Conversation.query.get(conversation_id)
    if conversation:
        # Check if conversation belongs to user's active unit (if authenticated)
        if user and conversation.unit_id != user.active_unit_id:
            logger.warning(f"Access denied to conversation {conversation_id}")
            return False
        
        db.session.delete(conversation)
        db.session.commit()
        logger.info(f"Conversation {conversation_id} deleted")
        return True
    logger.warning(f"Conversation {conversation_id} not found for deletion")
    return False

def get_conversation_messages(conversation_id):
    logger.info(f"Fetching messages for conversation: {conversation_id}")
    return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).all()
