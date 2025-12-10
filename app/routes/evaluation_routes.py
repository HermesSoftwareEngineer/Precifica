from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.controllers.evaluation_controller import (
    create_evaluation, get_evaluations, get_evaluation, update_evaluation, delete_evaluation,
    create_base_listing, get_base_listings, get_base_listing, update_base_listing, delete_base_listing
)
import logging

logger = logging.getLogger(__name__)

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api/evaluations')

# Evaluation Routes
@evaluation_bp.route('/', methods=['POST'])
@jwt_required()
def create_evaluation_route():
    logger.info("Create evaluation route accessed")
    return create_evaluation()

@evaluation_bp.route('/', methods=['GET'])
@jwt_required()
def get_evaluations_route():
    logger.info("Get evaluations route accessed")
    return get_evaluations()

@evaluation_bp.route('/<int:evaluation_id>', methods=['GET'])
@jwt_required()
def get_evaluation_route(evaluation_id):
    logger.info(f"Get evaluation route accessed for id: {evaluation_id}")
    return get_evaluation(evaluation_id)

@evaluation_bp.route('/<int:evaluation_id>', methods=['PUT'])
@jwt_required()
def update_evaluation_route(evaluation_id):
    logger.info(f"Update evaluation route accessed for id: {evaluation_id}")
    return update_evaluation(evaluation_id)

@evaluation_bp.route('/<int:evaluation_id>', methods=['DELETE'])
@jwt_required()
def delete_evaluation_route(evaluation_id):
    logger.info(f"Delete evaluation route accessed for id: {evaluation_id}")
    return delete_evaluation(evaluation_id)

# Base Listing Routes (Nested under evaluations for creation/listing)
@evaluation_bp.route('/<int:evaluation_id>/listings', methods=['POST'])
@jwt_required()
def create_base_listing_route(evaluation_id):
    logger.info(f"Create base listing route accessed for evaluation: {evaluation_id}")
    return create_base_listing(evaluation_id)

@evaluation_bp.route('/<int:evaluation_id>/listings', methods=['GET'])
@jwt_required()
def get_base_listings_route(evaluation_id):
    logger.info(f"Get base listings route accessed for evaluation: {evaluation_id}")
    return get_base_listings(evaluation_id)

# Base Listing Routes (Direct access for update/delete/get single)
@evaluation_bp.route('/listings/<int:listing_id>', methods=['GET'])
@jwt_required()
def get_base_listing_route(listing_id):
    logger.info(f"Get base listing route accessed for listing: {listing_id}")
    return get_base_listing(listing_id)

@evaluation_bp.route('/listings/<int:listing_id>', methods=['PUT'])
@jwt_required()
def update_base_listing_route(listing_id):
    logger.info(f"Update base listing route accessed for listing: {listing_id}")
    return update_base_listing(listing_id)

@evaluation_bp.route('/listings/<int:listing_id>', methods=['DELETE'])
@jwt_required()
def delete_base_listing_route(listing_id):
    logger.info(f"Delete base listing route accessed for listing: {listing_id}")
    return delete_base_listing(listing_id)
