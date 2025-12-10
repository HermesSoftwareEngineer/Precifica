from flask import Blueprint
from app.controllers.bot_controller import chat, chat_evaluation
import logging

logger = logging.getLogger(__name__)

bot_bp = Blueprint('bot', __name__, url_prefix='/bot')

@bot_bp.route('/chat', methods=['POST'])
def chat_route():
    logger.info("Chat route accessed")
    return chat()

@bot_bp.route('/evaluation/<int:evaluation_id>/chat', methods=['POST'])
def chat_evaluation_route(evaluation_id):
    logger.info(f"Chat evaluation route accessed for evaluation_id: {evaluation_id}")
    return chat_evaluation(evaluation_id)
