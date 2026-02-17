from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.controllers.evaluation_controller import (
    create_evaluation, get_evaluations, get_evaluation, update_evaluation, delete_evaluation,
    create_base_listing, get_base_listings, get_base_listing, update_base_listing, delete_base_listing
)
from app.controllers.bot_controller import run_evaluation_chat, enqueue_evaluation_chat
from app.services.sse import register_listener, remove_listener, publish_event, format_sse
from app.services.ai_cancel import cancel_evaluation, clear_evaluation_cancel
from app.utils.unit_helpers import get_user_with_active_unit
from queue import Empty
import logging

logger = logging.getLogger(__name__)

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api/evaluations')

def _build_ai_prompt(evaluation_data):
    parts = []
    fields = [
        ("endereco", "address"),
        ("bairro", "neighborhood"),
        ("cidade", "city"),
        ("estado", "state"),
        ("area", "area"),
        ("classificacao", "classification"),
        ("finalidade", "purpose"),
        ("tipo", "property_type"),
        ("quartos", "bedrooms"),
        ("banheiros", "bathrooms"),
        ("vagas", "parking_spaces")
    ]

    for label, key in fields:
        value = evaluation_data.get(key)
        if value not in (None, ""):
            parts.append(f"{label}: {value}")

    details = "; ".join(parts) if parts else "sem detalhes adicionais"
    return (
        "Voce esta iniciando a pesquisa de amostras para a avaliacao recem-criada. "
        "Siga o processo de nova avaliacao: "
        "1) Pesquise 15-25 imoveis comparaveis no mesmo bairro e cidade com pesquisar_sites; "
        "2) Abra 2-3 links com ler_conteudo_site para extrair dados; "
        "3) Para cada imovel reconhecido, capture link, endereco/bairro/cidade, area, valor total (venda/aluguel), "
        "quartos, banheiros, vagas e condominio quando houver; "
        "4) Filtre: area +/-60%, quartos/banheiros/vagas +/-3, remova outliers de valor/m2; "
        "5) Adicione as amostras UMA A UMA com adicionar_imoveis_base assim que cada imovel valido for reconhecido; "
        "6) Mantenha 10-20 imoveis semelhantes e continue adicionando ate completar a amostra; "
        "7) Nao peca dados ao usuario, use os dados da avaliacao. "
        f"Dados do imovel alvo: {details}."
    )

# Evaluation Routes
@evaluation_bp.route('/', methods=['POST'])
@jwt_required()
def create_evaluation_route():
    logger.info("Create evaluation route accessed")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return create_evaluation()

@evaluation_bp.route('/ai', methods=['POST'])
@jwt_required()
def create_evaluation_with_ai_route():
    logger.info("Create evaluation with AI route accessed")
    user, error = get_user_with_active_unit()
    if error:
        return error
    data = request.get_json() or {}
    ai_prompt = data.pop('ai_prompt', None)
    ai_force_new_chat = data.pop('ai_force_new_chat', True)

    response, status_code = create_evaluation(data)
    if status_code != 201:
        return response, status_code

    evaluation_data = response.get_json()
    evaluation_id = evaluation_data.get('id')
    clear_evaluation_cancel(evaluation_id)
    if not ai_prompt:
        ai_prompt = _build_ai_prompt(evaluation_data)

    publish_event(f"evaluation:{evaluation_id}", "evaluation_created", evaluation_data)

    user_id = None
    try:
        user_id = int(get_jwt_identity())
    except Exception:
        user_id = None

    ai_response, ai_status = run_evaluation_chat(
        evaluation_id,
        ai_prompt,
        force_new_chat=ai_force_new_chat,
        user_id=user_id
    )

    if ai_status >= 400:
        ai_error = None
        try:
            ai_error = ai_response.get_json().get('error')
        except Exception:
            ai_error = 'AI request failed'

        return jsonify({
            'evaluation': evaluation_data,
            'ai_error': ai_error
        }), 201

    return jsonify({
        'evaluation': evaluation_data,
        'ai': ai_response.get_json()
    }), 201

@evaluation_bp.route('/ai/async', methods=['POST'])
@jwt_required()
def create_evaluation_with_ai_async_route():
    logger.info("Create evaluation with AI async route accessed")
    user, error = get_user_with_active_unit()
    if error:
        return error
    data = request.get_json() or {}
    ai_prompt = data.pop('ai_prompt', None)
    ai_force_new_chat = data.pop('ai_force_new_chat', True)

    response, status_code = create_evaluation(data)
    if status_code != 201:
        return response, status_code

    evaluation_data = response.get_json()
    evaluation_id = evaluation_data.get('id')
    clear_evaluation_cancel(evaluation_id)
    if not ai_prompt:
        ai_prompt = _build_ai_prompt(evaluation_data)

    publish_event(f"evaluation:{evaluation_id}", "evaluation_created", evaluation_data)

    user_id = None
    try:
        user_id = int(get_jwt_identity())
    except Exception:
        user_id = None

    conversation, user_msg, error_response, error_status = enqueue_evaluation_chat(
        evaluation_id,
        ai_prompt,
        force_new_chat=ai_force_new_chat,
        user_id=user_id
    )
    if error_response:
        return error_response, error_status

    publish_event(
        f"evaluation:{evaluation_id}",
        "ai_queued",
        {
            "conversation_id": conversation.id,
            "message_id": user_msg.id
        }
    )

    return jsonify({
        'status': 'queued',
        'evaluation': evaluation_data,
        'conversation_id': conversation.id,
        'message_id': user_msg.id
    }), 202

@evaluation_bp.route('/<int:evaluation_id>/ai/stream', methods=['GET'])
@jwt_required()
def stream_evaluation_ai_events(evaluation_id):
    def event_stream():
        channel_key = f"evaluation:{evaluation_id}"
        queue = register_listener(channel_key)
        try:
            yield format_sse("connected", {"evaluation_id": evaluation_id})
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

@evaluation_bp.route('/<int:evaluation_id>/ai/cancel', methods=['POST'])
@jwt_required()
def cancel_evaluation_ai_route(evaluation_id):
    user, error = get_user_with_active_unit()
    if error:
        return error
    cancel_evaluation(evaluation_id)
    publish_event(f"evaluation:{evaluation_id}", "cancelled", {"reason": "user_requested"})
    return jsonify({'status': 'cancelled', 'evaluation_id': evaluation_id}), 200

@evaluation_bp.route('/', methods=['GET'])
@jwt_required()
def get_evaluations_route():
    logger.info("Get evaluations route accessed")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return get_evaluations()

@evaluation_bp.route('/<int:evaluation_id>', methods=['GET'])
@jwt_required()
def get_evaluation_route(evaluation_id):
    logger.info(f"Get evaluation route accessed for id: {evaluation_id}")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return get_evaluation(evaluation_id)

@evaluation_bp.route('/<int:evaluation_id>', methods=['PUT'])
@jwt_required()
def update_evaluation_route(evaluation_id):
    logger.info(f"Update evaluation route accessed for id: {evaluation_id}")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return update_evaluation(evaluation_id)

@evaluation_bp.route('/<int:evaluation_id>', methods=['DELETE'])
@jwt_required()
def delete_evaluation_route(evaluation_id):
    logger.info(f"Delete evaluation route accessed for id: {evaluation_id}")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return delete_evaluation(evaluation_id)

# Base Listing Routes (Nested under evaluations for creation/listing)
@evaluation_bp.route('/<int:evaluation_id>/listings', methods=['POST'])
@jwt_required()
def create_base_listing_route(evaluation_id):
    logger.info(f"Create base listing route accessed for evaluation: {evaluation_id}")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return create_base_listing(evaluation_id)

@evaluation_bp.route('/<int:evaluation_id>/listings', methods=['GET'])
@jwt_required()
def get_base_listings_route(evaluation_id):
    logger.info(f"Get base listings route accessed for evaluation: {evaluation_id}")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return get_base_listings(evaluation_id)

# Base Listing Routes (Direct access for update/delete/get single)
@evaluation_bp.route('/listings/<int:listing_id>', methods=['GET'])
@jwt_required()
def get_base_listing_route(listing_id):
    logger.info(f"Get base listing route accessed for listing: {listing_id}")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return get_base_listing(listing_id)

@evaluation_bp.route('/listings/<int:listing_id>', methods=['PUT'])
@jwt_required()
def update_base_listing_route(listing_id):
    logger.info(f"Update base listing route accessed for listing: {listing_id}")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return update_base_listing(listing_id)

@evaluation_bp.route('/listings/<int:listing_id>', methods=['DELETE'])
@jwt_required()
def delete_base_listing_route(listing_id):
    logger.info(f"Delete base listing route accessed for listing: {listing_id}")
    user, error = get_user_with_active_unit()
    if error:
        return error
    return delete_base_listing(listing_id)
