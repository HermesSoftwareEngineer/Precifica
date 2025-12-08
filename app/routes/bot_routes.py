from flask import Blueprint
from app.controllers.bot_controller import chat, chat_evaluation

bot_bp = Blueprint('bot', __name__, url_prefix='/bot')

bot_bp.route('/chat', methods=['POST'])(chat)
bot_bp.route('/evaluation/<int:evaluation_id>/chat', methods=['POST'])(chat_evaluation)
