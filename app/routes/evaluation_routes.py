from flask import Blueprint
from app.controllers.evaluation_controller import (
    create_evaluation, get_evaluations, get_evaluation, update_evaluation, delete_evaluation,
    create_base_listing, get_base_listings, get_base_listing, update_base_listing, delete_base_listing
)

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api/evaluations')

# Evaluation Routes
evaluation_bp.route('/', methods=['POST'])(create_evaluation)
evaluation_bp.route('/', methods=['GET'])(get_evaluations)
evaluation_bp.route('/<int:evaluation_id>', methods=['GET'])(get_evaluation)
evaluation_bp.route('/<int:evaluation_id>', methods=['PUT'])(update_evaluation)
evaluation_bp.route('/<int:evaluation_id>', methods=['DELETE'])(delete_evaluation)

# Base Listing Routes (Nested under evaluations for creation/listing)
evaluation_bp.route('/<int:evaluation_id>/listings', methods=['POST'])(create_base_listing)
evaluation_bp.route('/<int:evaluation_id>/listings', methods=['GET'])(get_base_listings)

# Base Listing Routes (Direct access for update/delete/get single)
# Note: We could also nest these, but direct access by ID is often cleaner if IDs are unique globally (which they are)
# However, to keep it organized, I'll put them under a separate prefix or just handle them here.
# Let's add a separate route group or just add them to the same blueprint but with different paths.
# Since listing_id is unique, we can just use /listings/<id>
evaluation_bp.route('/listings/<int:listing_id>', methods=['GET'])(get_base_listing)
evaluation_bp.route('/listings/<int:listing_id>', methods=['PUT'])(update_base_listing)
evaluation_bp.route('/listings/<int:listing_id>', methods=['DELETE'])(delete_base_listing)
