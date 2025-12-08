from app.extensions import db
from app.models.chat import Conversation, Message
from flask_login import current_user

def create_conversation(title="New Conversation"):
    user_id = current_user.id if current_user.is_authenticated else None
    conversation = Conversation(user_id=user_id, title=title)
    db.session.add(conversation)
    db.session.commit()
    return conversation

def get_user_conversations():
    if not current_user.is_authenticated:
        return []
    return Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()

def get_conversation_by_id(conversation_id):
    return Conversation.query.get(conversation_id)

def update_conversation_title(conversation_id, new_title):
    conversation = Conversation.query.get(conversation_id)
    if conversation:
        conversation.title = new_title
        db.session.commit()
    return conversation

def delete_conversation_by_id(conversation_id):
    conversation = Conversation.query.get(conversation_id)
    if conversation:
        db.session.delete(conversation)
        db.session.commit()
        return True
    return False

def get_conversation_messages(conversation_id):
    return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.asc()).all()
