import sys
import os
import logging
from threading import Thread
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)

# Adiciona o diretório app/bot ao sys.path para resolver as importações internas do bot
current_dir = os.path.dirname(os.path.abspath(__file__))
bot_dir = os.path.join(os.path.dirname(current_dir), 'bot')
if bot_dir not in sys.path:
    sys.path.append(bot_dir)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.bot.mainGraph import graph
from app.bot.prompts import prompt_ajuste_avaliacao
from app.bot.llms import llm_main
from app.models.chat import Conversation, Message
from app.models.evaluation import Evaluation
from app.models.user import User
from app.extensions import db
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from app.services.sse import publish_event
from app.services.ai_cancel import is_evaluation_canceled, clear_evaluation_cancel

def generate_conversation_title(user_message):
    try:
        prompt = ChatPromptTemplate.from_template(
            "Gere um título curto (máximo 5 palavras) e conciso para uma conversa que começa com a seguinte mensagem: {message}. Responda apenas com o título."
        )
        chain = prompt | llm_main | StrOutputParser()
        title = chain.invoke({"message": user_message})
        return title.strip()
    except Exception as e:
        logger.error(f"Error generating title: {e}")
        return "Nova Conversa"

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
        
        # Update title if it's the first message and title is default
        if conversation.title == "New Conversation" and not conversation.messages:
             conversation.title = generate_conversation_title(user_input)
             db.session.commit()
    else:
        # Create new conversation
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            unit_id = user.active_unit_id if user else None
        except:
            user_id = None
            unit_id = None
        logger.info(f"Creating new conversation for user: {user_id}, unit: {unit_id}")
        title = generate_conversation_title(user_input)
        conversation = Conversation(user_id=user_id, unit_id=unit_id, title=title)
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

def _extract_ai_message(ai_message_content):
    if isinstance(ai_message_content, list):
        text_parts = []
        for block in ai_message_content:
            if isinstance(block, dict) and 'text' in block:
                text_parts.append(block['text'])
            elif isinstance(block, str):
                text_parts.append(block)
        return "\n".join(text_parts)
    return str(ai_message_content)

def _start_background_response(app, conversation_id, full_input, channel_key, use_tuple_list, evaluation_id=None):
    def run():
        with app.app_context():
            def publish_cancel_message(conversation):
                cancel_text = (
                    "Pesquisa cancelada pelo usuario. "
                    "As amostras coletadas ate aqui foram mantidas."
                )
                bot_msg = Message(conversation_id=conversation.id, sender='bot', content=cancel_text)
                db.session.add(bot_msg)
                conversation.updated_at = datetime.utcnow()
                db.session.commit()
                publish_event(
                    channel_key,
                    "ai_message",
                    {
                        "message": bot_msg.to_dict(),
                        "conversation": conversation.to_dict()
                    }
                )

            if evaluation_id is not None and is_evaluation_canceled(evaluation_id):
                conversation = Conversation.query.get(conversation_id)
                if conversation:
                    publish_cancel_message(conversation)
                publish_event(
                    f"evaluation:{evaluation_id}",
                    "cancelled",
                    {"reason": "user_requested"}
                )
                return

            conversation = Conversation.query.get(conversation_id)
            if not conversation:
                publish_event(channel_key, "error", {"error": "Conversation not found"})
                if evaluation_id is not None:
                    publish_event(f"evaluation:{evaluation_id}", "error", {"error": "Conversation not found"})
                return

            config = {
                "configurable": {"thread_id": str(conversation.id)},
                "recursion_limit": 100
            }
            try:
                if use_tuple_list:
                    response = graph.invoke({"messages": [("user", full_input)]}, config)
                else:
                    response = graph.invoke({"messages": full_input}, config)

                ai_message_content = response["messages"][-1].content
                ai_message = _extract_ai_message(ai_message_content)

                if evaluation_id is not None and is_evaluation_canceled(evaluation_id):
                    publish_cancel_message(conversation)
                    publish_event(
                        f"evaluation:{evaluation_id}",
                        "cancelled",
                        {"reason": "user_requested"}
                    )
                    return

                bot_msg = Message(conversation_id=conversation.id, sender='bot', content=ai_message)
                db.session.add(bot_msg)
                conversation.updated_at = datetime.utcnow()
                db.session.commit()

                publish_event(
                    channel_key,
                    "ai_message",
                    {
                        "message": bot_msg.to_dict(),
                        "conversation": conversation.to_dict()
                    }
                )

                if evaluation_id is not None:
                    publish_event(
                        f"evaluation:{evaluation_id}",
                        "done",
                        {
                            "conversation_id": conversation.id,
                            "message_id": bot_msg.id
                        }
                    )
                    clear_evaluation_cancel(evaluation_id)

            except Exception as e:
                logger.error(f"Error in background bot chat: {e}", exc_info=True)
                publish_event(channel_key, "error", {"error": str(e)})
                if evaluation_id is not None:
                    publish_event(f"evaluation:{evaluation_id}", "error", {"error": str(e)})

    thread = Thread(target=run, daemon=True)
    thread.start()

def chat_async():
    logger.info("Starting async chat request processing")
    data = request.get_json() or {}
    user_input = data.get('message')
    conversation_id = data.get('conversation_id')

    if not user_input:
        logger.warning("Message is required but missing")
        return jsonify({'error': 'Message is required'}), 400

    conversation = None
    if conversation_id:
        logger.info(f"Retrieving conversation: {conversation_id}")
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            logger.warning(f"Conversation not found: {conversation_id}")
            return jsonify({'error': 'Conversation not found'}), 404

        if conversation.title == "New Conversation" and not conversation.messages:
            conversation.title = generate_conversation_title(user_input)
            db.session.commit()
    else:
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            unit_id = user.active_unit_id if user else None
        except Exception:
            user_id = None
            unit_id = None
        logger.info(f"Creating new conversation for user: {user_id}, unit: {unit_id}")
        title = generate_conversation_title(user_input)
        conversation = Conversation(user_id=user_id, unit_id=unit_id, title=title)
        db.session.add(conversation)
        db.session.commit()
        conversation_id = conversation.id
        logger.info(f"New conversation created: {conversation_id}")

    user_msg = Message(conversation_id=conversation.id, sender='user', content=user_input)
    db.session.add(user_msg)
    db.session.commit()

    channel_key = f"conversation:{conversation.id}"
    publish_event(
        channel_key,
        "user_message",
        {
            "message": user_msg.to_dict(),
            "conversation": conversation.to_dict()
        }
    )

    app = current_app._get_current_object()
    _start_background_response(app, conversation.id, user_input, channel_key, use_tuple_list=False)

    return jsonify({
        'status': 'queued',
        'conversation_id': conversation.id,
        'message_id': user_msg.id
    }), 202

def run_evaluation_chat(evaluation_id, user_input, force_new_chat=False, user_id=None):
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
        if user_id is None:
            try:
                verify_jwt_in_request()
                user_id = int(get_jwt_identity())
            except Exception:
                user_id = None
        
        # Get unit_id from evaluation
        unit_id = evaluation.unit_id

        conversation = Conversation(user_id=user_id, unit_id=unit_id, title=f"Ajuste Avaliacao #{evaluation_id}", evaluation_id=evaluation_id)
        db.session.add(conversation)
        db.session.flush()

        evaluation.last_chat_id = conversation.id
        db.session.commit()
        logger.info(f"New conversation created: {conversation.id}, unit: {unit_id}")

    # 2. Preparar mensagem (Concatenar prompt se for nova conversa)
    if is_new_conversation:
        system_prompt = prompt_ajuste_avaliacao.format(evaluation_id=evaluation_id)
        full_input = f"{system_prompt}\n\nUser Input: {user_input}"
        logger.info("Injecting system prompt into first user message")
    else:
        full_input = user_input

    # 3. Salvar mensagem do usuario no banco (apenas o input original para nao poluir)
    user_msg = Message(conversation_id=conversation.id, sender='user', content=user_input)
    db.session.add(user_msg)
    db.session.commit()

    # 4. Invocar o Graph
    config = {"configurable": {"thread_id": str(conversation.id)}}

    try:
        logger.info(f"Invoking graph for conversation {conversation.id}")

        # Envia full_input (com prompt se necessario) como mensagem de usuario
        response = graph.invoke({"messages": [("user", full_input)]}, config)

        # Extrair resposta
        last_message = response["messages"][-1]
        ai_message_content = last_message.content

        # Garantir que e string
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
        }), 200

    except Exception as e:
        logger.error(f"Error in bot chat evaluation: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def chat_evaluation(evaluation_id):
    logger.info(f"Starting chat evaluation for evaluation_id: {evaluation_id}")
    data = request.get_json()
    user_input = data.get('message')
    force_new_chat = data.get('new_chat', False)

    return run_evaluation_chat(evaluation_id, user_input, force_new_chat=force_new_chat)

def _prepare_evaluation_conversation(evaluation_id, user_input, force_new_chat=False, user_id=None):
    if not user_input:
        return None, None, jsonify({'error': 'Message is required'}), 400

    evaluation = Evaluation.query.get_or_404(evaluation_id)
    conversation = None
    if evaluation.last_chat_id and not force_new_chat:
        conversation = Conversation.query.get(evaluation.last_chat_id)

    is_new_conversation = False
    if not conversation:
        is_new_conversation = True
        if user_id is None:
            try:
                verify_jwt_in_request()
                user_id = int(get_jwt_identity())
            except Exception:
                user_id = None

        conversation = Conversation(user_id=user_id, title=f"Ajuste Avaliacao #{evaluation_id}", evaluation_id=evaluation_id)
        db.session.add(conversation)
        db.session.flush()

        evaluation.last_chat_id = conversation.id
        db.session.commit()

    if is_new_conversation:
        system_prompt = prompt_ajuste_avaliacao.format(evaluation_id=evaluation_id)
        full_input = f"{system_prompt}\n\nUser Input: {user_input}"
    else:
        full_input = user_input

    return conversation, full_input, None, 200

def chat_evaluation_async(evaluation_id):
    logger.info(f"Starting async chat evaluation for evaluation_id: {evaluation_id}")
    data = request.get_json() or {}
    user_input = data.get('message')
    force_new_chat = data.get('new_chat', False)

    conversation, full_input, error_response, status_code = _prepare_evaluation_conversation(
        evaluation_id,
        user_input,
        force_new_chat=force_new_chat
    )
    if error_response:
        return error_response, status_code

    user_msg = Message(conversation_id=conversation.id, sender='user', content=user_input)
    db.session.add(user_msg)
    db.session.commit()

    channel_key = f"conversation:{conversation.id}"
    publish_event(
        channel_key,
        "user_message",
        {
            "message": user_msg.to_dict(),
            "conversation": conversation.to_dict(),
            "evaluation_id": evaluation_id
        }
    )

    app = current_app._get_current_object()
    _start_background_response(
        app,
        conversation.id,
        full_input,
        channel_key,
        use_tuple_list=True,
        evaluation_id=evaluation_id
    )

    return jsonify({
        'status': 'queued',
        'conversation_id': conversation.id,
        'message_id': user_msg.id
    }), 202

def enqueue_evaluation_chat(evaluation_id, user_input, force_new_chat=False, user_id=None):
    clear_evaluation_cancel(evaluation_id)
    conversation, full_input, error_response, status_code = _prepare_evaluation_conversation(
        evaluation_id,
        user_input,
        force_new_chat=force_new_chat,
        user_id=user_id
    )
    if error_response:
        return None, None, error_response, status_code

    user_msg = Message(conversation_id=conversation.id, sender='user', content=user_input)
    db.session.add(user_msg)
    db.session.commit()

    channel_key = f"conversation:{conversation.id}"
    publish_event(
        channel_key,
        "user_message",
        {
            "message": user_msg.to_dict(),
            "conversation": conversation.to_dict(),
            "evaluation_id": evaluation_id
        }
    )

    app = current_app._get_current_object()
    _start_background_response(
        app,
        conversation.id,
        full_input,
        channel_key,
        use_tuple_list=True,
        evaluation_id=evaluation_id
    )

    return conversation, user_msg, None, 200
