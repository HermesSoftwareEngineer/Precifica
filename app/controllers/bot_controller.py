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
    
    if not user_input:
        return jsonify({'error': 'Message is required'}), 400

    evaluation = Evaluation.query.get_or_404(evaluation_id)
    
    # 1. Recuperar ou criar conversa
    conversation = None
    if evaluation.last_chat_id and not force_new_chat:
        conversation = Conversation.query.get(evaluation.last_chat_id)
    
    is_new_conversation = False
    if not conversation:
        is_new_conversation = True
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
        except:
            user_id = None
            
        conversation = Conversation(user_id=user_id, title=f"Ajuste Avaliação #{evaluation_id}", evaluation_id=evaluation_id)
        db.session.add(conversation)
        db.session.flush()
        
        evaluation.last_chat_id = conversation.id
        db.session.commit()
        logger.info(f"New conversation created: {conversation.id}")

    # 2. Preparar mensagem (Concatenar prompt se for nova conversa)
    if is_new_conversation:
        system_prompt = prompt_ajuste_avaliacao.format(evaluation_id=evaluation_id)
        full_input = f"{system_prompt}\n\nUser Input: {user_input}"
        logger.info("Injecting system prompt into first user message")
    else:
        full_input = user_input

    # 3. Salvar mensagem do usuário no banco (apenas o input original para não poluir)
    user_msg = Message(conversation_id=conversation.id, sender='user', content=user_input)
    db.session.add(user_msg)
    db.session.commit()

    # 4. Invocar o Graph
    config = {"configurable": {"thread_id": str(conversation.id)}}

    try:
        logger.info(f"Invoking graph for conversation {conversation.id}")
        
        # Envia full_input (com prompt se necessário) como mensagem de usuário
        response = graph.invoke({"messages": [("user", full_input)]}, config)
        
        # Extrair resposta
        last_message = response["messages"][-1]
        ai_message_content = last_message.content
        
        # Garantir que é string
        if isinstance(ai_message_content, list):
            text_parts = []
            for part in ai_message_content:
                if isinstance(part, dict) and part.get('type') == 'text':
                    text_parts.append(part.get('text', ''))
                elif isinstance(part, str):
                    text_parts.append(part)
            ai_message = "\n".join(text_parts)
        else:
            ai_message = str(ai_message_content)

        # 5. Salvar resposta do Bot
        bot_msg = Message(conversation_id=conversation.id, sender='bot', content=ai_message)
        db.session.add(bot_msg)
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'response': ai_message,
            'conversation_id': conversation.id,
            'message_id': bot_msg.id
        })

    except Exception as e:
        logger.error(f"Error in bot chat evaluation: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
