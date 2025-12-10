import sys
import os
import logging
from flask import request, jsonify

logger = logging.getLogger(__name__)

# Adiciona o diretório app/bot ao sys.path para resolver as importações internas do bot
current_dir = os.path.dirname(os.path.abspath(__file__))
bot_dir = os.path.join(os.path.dirname(current_dir), 'bot')
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

from app.bot.mainGraph import graph
from app.bot.prompts import prompt_ajuste_avaliacao
from app.models.chat import Conversation, Message
from app.models.evaluation import Evaluation
from app.extensions import db
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from datetime import datetime

def chat():
    logger.info("Starting chat request processing")
    data = request.get_json()
    user_input = data.get('message')
    conversation_id = data.get('conversation_id')
    
    # If no conversation_id, create a new one (if user is logged in, or handle anonymous)
    # For now, let's assume we want to persist everything.
    # If conversation_id is passed, verify it exists.
    
    conversation = None
    if conversation_id:
        logger.info(f"Retrieving conversation: {conversation_id}")
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
             logger.warning(f"Conversation not found: {conversation_id}")
             return jsonify({'error': 'Conversation not found'}), 404
    else:
        # Create new conversation
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
        except:
            user_id = None
        logger.info(f"Creating new conversation for user: {user_id}")
        conversation = Conversation(user_id=user_id, title=user_input[:30] + "...")
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
        logger.info(f"New conversation created: {conversation_id}")

    if not user_input:
        logger.warning("Message is required but missing")
        return jsonify({'error': 'Message is required'}), 400

    # Save User Message
    user_msg = Message(conversation_id=conversation.id, sender='user', content=user_input)
    db.session.add(user_msg)
    db.session.commit()
    logger.info(f"User message saved for conversation {conversation_id}")

    # Use conversation_id as thread_id for LangGraph memory
    config = {"configurable": {"thread_id": str(conversation.id)}}

    try:
        # O input para o graph deve ser compatível com o que está definido no State
        logger.info(f"Invoking graph for conversation {conversation_id}")
        response = graph.invoke({"messages": user_input}, config)
        
        # Extrai a última mensagem que deve ser a resposta da IA
        ai_message_content = response['messages'][-1].content
        
        # Process content to ensure it's a string for the database
        if isinstance(ai_message_content, list):
            # Handle list of content blocks (e.g. [{'type': 'text', 'text': '...'}])
            text_parts = []
            for block in ai_message_content:
                if isinstance(block, dict) and 'text' in block:
                    text_parts.append(block['text'])
                elif isinstance(block, str):
                    text_parts.append(block)
            ai_message = "\n".join(text_parts)
        else:
            ai_message = str(ai_message_content)
        
        # Save Bot Message
        bot_msg = Message(conversation_id=conversation.id, sender='bot', content=ai_message)
        db.session.add(bot_msg)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"Bot response saved for conversation {conversation_id}")
        
        return jsonify({
            'response': ai_message,
            'conversation_id': conversation.id,
            'message_id': bot_msg.id
        })

    except Exception as e:
        logger.error(f"Error in bot chat: {e}", exc_info=True)
        print(f"Error in bot chat: {e}")
        return jsonify({'error': str(e)}), 500

def chat_evaluation(evaluation_id):
    logger.info(f"Starting chat evaluation for evaluation_id: {evaluation_id}")
    data = request.get_json()
    user_input = data.get('message')
    force_new_chat = data.get('new_chat', False)
    
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    
    conversation = None
    if evaluation.last_chat_id and not force_new_chat:
        logger.info(f"Retrieving last chat for evaluation: {evaluation.last_chat_id}")
        conversation = Conversation.query.get(evaluation.last_chat_id)
    
    if not conversation:
        # Create new conversation
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
        except:
            user_id = None
        conversation = Conversation(user_id=user_id, title=f"Ajuste Avaliação #{evaluation_id}")
        db.session.add(conversation)
        db.session.flush() # Get ID
        
        # Update evaluation with new chat ID
        evaluation.last_chat_id = conversation.id
        
        # Add System Prompt
        system_content = prompt_ajuste_avaliacao.format(evaluation_id=evaluation_id)
        system_msg = Message(conversation_id=conversation.id, sender='system', content=system_content)
        db.session.add(system_msg)
        
        db.session.commit()

    if not user_input:
        return jsonify({'error': 'Message is required'}), 400

    # Save User Message
    user_msg = Message(conversation_id=conversation.id, sender='user', content=user_input)
    db.session.add(user_msg)
    db.session.commit()

    # Use conversation_id as thread_id for LangGraph memory
    config = {"configurable": {"thread_id": str(conversation.id)}}

    try:
        # Invoke graph
        # We need to pass the history or let the memory handle it.
        # Since we are using MemorySaver with thread_id, we just need to pass the new message.
        # However, for the FIRST message in a new conversation, we might want to ensure the system prompt is included in the context.
        # If we just added it to the DB, the graph memory might not know about it yet if it only reads from its own checkpoint.
        # But wait, the graph uses `MemorySaver` which stores state in memory (RAM) usually, unless configured to use DB.
        # Here `memory = MemorySaver()` in `mainGraph.py`.
        # So the graph state is separate from the DB `Message` table.
        # We need to sync them or just pass the messages to the graph.
        
        # If it's a new conversation (or we are restarting the server), the memory might be empty.
        # We should probably pass the system message if it's the first turn.
        
        messages_to_send = []
        if len(conversation.messages) <= 2: # System + User (just added)
             # Fetch system message
             sys_msg = Message.query.filter_by(conversation_id=conversation.id, sender='system').first()
             if sys_msg:
                 messages_to_send.append(("system", sys_msg.content))
        
        messages_to_send.append(("user", user_input))
        
        result = graph.invoke({"messages": messages_to_send}, config)
        
        # Extract response
        last_message = result["messages"][-1]
        ai_message = last_message.content
        
        # Ensure ai_message is a string
        if isinstance(ai_message, list):
            # If it's a list (e.g. from Gemini with thought process), extract the text part
            text_parts = []
            for part in ai_message:
                if isinstance(part, dict) and part.get('type') == 'text':
                    text_parts.append(part.get('text', ''))
                elif isinstance(part, str):
                    text_parts.append(part)
            ai_message = "\n".join(text_parts)
        elif not isinstance(ai_message, str):
             ai_message = str(ai_message)

        # Save Bot Message
        bot_msg = Message(conversation_id=conversation.id, sender='bot', content=ai_message)
        db.session.add(bot_msg)
        db.session.commit()
        
        return jsonify({
            'response': ai_message,
            'conversation_id': conversation.id,
            'message_id': bot_msg.id
        })

    except Exception as e:
        print(f"Error in bot chat evaluation: {e}")
        return jsonify({'error': str(e)}), 500
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500
