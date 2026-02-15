from flask import Blueprint, Response, stream_with_context, jsonify
from app.controllers.bot_controller import chat, chat_evaluation, chat_async, chat_evaluation_async
from app.models.chat import Conversation
from app.services.sse import register_listener, remove_listener, format_sse
from queue import Empty
import logging

logger = logging.getLogger(__name__)

bot_bp = Blueprint('bot', __name__, url_prefix='/bot')

@bot_bp.route('/chat', methods=['POST'])
def chat_route():
    logger.info("Chat route accessed")
    return chat()

@bot_bp.route('/chat/async', methods=['POST'])
def chat_async_route():
    logger.info("Chat async route accessed")
    return chat_async()

@bot_bp.route('/evaluation/<int:evaluation_id>/chat', methods=['POST'])
def chat_evaluation_route(evaluation_id):
    logger.info(f"Chat evaluation route accessed for evaluation_id: {evaluation_id}")
    return chat_evaluation(evaluation_id)

@bot_bp.route('/evaluation/<int:evaluation_id>/chat/async', methods=['POST'])
def chat_evaluation_async_route(evaluation_id):
    logger.info(f"Chat evaluation async route accessed for evaluation_id: {evaluation_id}")
    return chat_evaluation_async(evaluation_id)

@bot_bp.route('/conversations/<int:conversation_id>/stream', methods=['GET'])
def stream_conversation_events(conversation_id):
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404

    def event_stream():
        channel_key = f"conversation:{conversation_id}"
        queue = register_listener(channel_key)
        try:
            yield format_sse("connected", {"conversation_id": conversation_id})
            while True:
                try:
                    payload = queue.get(timeout=15)
                except Empty:
                    yield ": ping\n\n"
                    continue

                yield format_sse(payload["event"], payload["data"])
        except GeneratorExit:
            pass
        finally:
            remove_listener(channel_key, queue)

    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')
