from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.evaluation import Evaluation, BaseListing
from app.models.user import User
from app.extensions import db, bot_user_id_var
from app.services.sse import publish_event
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _get_current_user_id():
    """Return the current user_id from the JWT token or the bot context variable.

    Controller functions may be called from two contexts:
    1. A normal HTTP request decorated with @jwt_required() — get_jwt_identity() works.
    2. A bot background thread (no request context) — fall back to bot_user_id_var.
    """
    context_user_id = bot_user_id_var.get()
    if context_user_id is not None:
        return int(context_user_id)

    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id is not None:
            return int(user_id)
    except Exception:
        pass

    return None

def normalize_purpose(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    normalized = value.strip()
    lowered = normalized.lower()

    if "residential" in lowered and "commercial" in lowered:
        return "Residencial / Comercial"
    if "residencial" in lowered and "comercial" in lowered:
        return "Residencial / Comercial"
    if "residential" in lowered or "residencial" in lowered:
        return "Residencial"
    if "commercial" in lowered or "comercial" in lowered:
        return "Comercial"

    return normalized

def normalize_property_type(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    normalized = value.strip()
    lowered = normalized.lower()

    mapping = [
        ("apartamento", "Apartamento"),
        ("apartment", "Apartamento"),
        ("casa", "Casa"),
        ("house", "Casa"),
        ("kitnet", "Kitnet"),
        ("loja", "Loja"),
        ("store", "Loja"),
        ("sala", "Sala"),
        ("office", "Sala"),
        ("terreno", "Terreno"),
        ("land", "Terreno")
    ]

    found = []
    for key, label in mapping:
        if key in lowered and label not in found:
            found.append(label)

    if found:
        return " / ".join(found)

    return normalized


def normalize_classification(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    normalized = value.strip()
    lowered = normalized.lower()

    if lowered in ("", "none", "null"):
        return "sale"
    if "venda" in lowered or "sale" in lowered:
        return "sale"
    if "aluguel" in lowered or "rent" in lowered:
        return "rent"

    return normalized


def _calculate_evaluation_metrics_for_states(evaluation, listings_state):
    """
    Calculate evaluation metrics using a custom active/inactive state map.
    This is used for preview mode (without persisting to the database).
    """
    listings = [
        listing
        for listing in evaluation.base_listings
        if listings_state.get(listing.id, {}).get('is_active', listing.is_active)
    ]

    analyzed_properties_count = len(listings)
    total_sqm_value = 0.0
    valid_listings_count = 0

    for listing in listings:
        if listing.rent_value and listing.area and listing.area > 0:
            sqm_value = listing.rent_value / listing.area
            total_sqm_value += sqm_value
            valid_listings_count += 1

    region_value_sqm = (total_sqm_value / valid_listings_count) if valid_listings_count > 0 else 0.0

    if evaluation.area:
        estimated_price = evaluation.area * region_value_sqm
        rounded_price = evaluation.calculate_rounded_price(estimated_price)
    else:
        estimated_price = 0.0
        rounded_price = 0.0

    total_listings_count = len(evaluation.base_listings)
    active_listings_count = analyzed_properties_count
    inactive_listings_count = total_listings_count - active_listings_count

    return {
        'region_value_sqm': region_value_sqm,
        'estimated_price': estimated_price,
        'rounded_price': rounded_price,
        'analyzed_properties_count': analyzed_properties_count,
        'active_listings_count': active_listings_count,
        'inactive_listings_count': inactive_listings_count,
        'total_listings_count': total_listings_count
    }


def _build_listing_state_map(evaluation):
    return {
        listing.id: {
            'is_active': listing.is_active,
            'deactivation_reason': listing.deactivation_reason
        }
        for listing in evaluation.base_listings
    }


def _get_current_user_with_active_unit():
    user_id = _get_current_user_id()
    if user_id is None:
        return None, (jsonify({'error': 'Authentication required'}), 401)

    user = User.query.get(user_id)
    if not user or not user.active_unit_id:
        return None, (jsonify({'error': 'No active unit selected'}), 400)

    return user, None


def _get_evaluation_for_user_or_error(evaluation_id, user):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    if evaluation.unit_id != user.active_unit_id:
        return None, (jsonify({'error': 'Access denied'}), 403)
    return evaluation, None


def _get_listing_for_user_or_error(listing_id, user):
    listing = BaseListing.query.get_or_404(listing_id)
    if not listing.evaluation or listing.evaluation.unit_id != user.active_unit_id:
        return None, (jsonify({'error': 'Access denied'}), 403)
    return listing, None

# --- Evaluation CRUD ---

def create_evaluation(data=None):
    logger.info("Creating new evaluation")
    if data is None:
        data = request.get_json()
    try:
        # Get user's active unit
        user_id = _get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        user = User.query.get(user_id)
        if not user or not user.active_unit_id:
            return jsonify({'error': 'No active unit selected'}), 400
        
        purpose = normalize_purpose(data.get('purpose'))
        property_type = normalize_property_type(data.get('property_type'))
        classification = normalize_classification(data.get('classification'))
        new_evaluation = Evaluation(
            unit_id=user.active_unit_id,
            address=data.get('address'),
            neighborhood=data.get('neighborhood'),
            city=data.get('city'),
            state=data.get('state'),
            area=data.get('area'),
            region_value_sqm=data.get('region_value_sqm'),
            analysis_type=data.get('analysis_type'),
            owner_name=data.get('owner_name'),
            appraiser_name=data.get('appraiser_name'),
            estimated_price=data.get('estimated_price'),
            rounded_price=None,
            description=data.get('description'),
            classification=classification,
            purpose=purpose,
            property_type=property_type,
            bedrooms=data.get('bedrooms', 0),
            bathrooms=data.get('bathrooms', 0),
            parking_spaces=data.get('parking_spaces', 0),
            analyzed_properties_count=data.get('analyzed_properties_count', 0),
            depreciation=data.get('depreciation', 0.0)
        )

        if new_evaluation.estimated_price is None and new_evaluation.area and new_evaluation.region_value_sqm:
            new_evaluation.estimated_price = new_evaluation.area * new_evaluation.region_value_sqm

        new_evaluation.recalculate_rounded_price()

        db.session.add(new_evaluation)
        db.session.commit()
        logger.info(f"Evaluation created successfully: {new_evaluation.id}")
        return jsonify(new_evaluation.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating evaluation: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def get_evaluations():
    logger.info("Fetching all evaluations")
    
    # Get user's active unit
    user_id = _get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Authentication required'}), 401
    user = User.query.get(user_id)
    if not user or not user.active_unit_id:
        return jsonify({'error': 'No active unit selected'}), 400
    
    # Filter by user's active unit
    query = Evaluation.query.filter(Evaluation.unit_id == user.active_unit_id)
    
    classification = request.args.get('classification')
    purpose = normalize_purpose(request.args.get('purpose'))
    appraiser_name = request.args.get('appraiser_name')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    sort_dir = request.args.get('sort_dir', default='desc')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)

    if classification:
        query = query.filter(Evaluation.classification.ilike(f"%{classification}%"))

    if purpose:
        query = query.filter(Evaluation.purpose.ilike(f"%{purpose}%"))

    if appraiser_name:
        query = query.filter(Evaluation.appraiser_name.ilike(f"%{appraiser_name}%"))

    if min_price is not None:
        query = query.filter(Evaluation.rounded_price >= min_price)

    if max_price is not None:
        query = query.filter(Evaluation.rounded_price <= max_price)

    def parse_date(date_str, is_end=False):
        if not date_str:
            return None
        try:
            parsed = datetime.fromisoformat(date_str)
        except ValueError:
            return None
        if 'T' not in date_str and len(date_str) <= 10:
            if is_end:
                return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
            return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
        return parsed

    start_date = parse_date(start_date_str, is_end=False)
    end_date = parse_date(end_date_str, is_end=True)

    if start_date_str and start_date is None:
        return jsonify({'error': 'Invalid start_date format'}), 400

    if end_date_str and end_date is None:
        return jsonify({'error': 'Invalid end_date format'}), 400

    if start_date:
        query = query.filter(Evaluation.created_at >= start_date)

    if end_date:
        query = query.filter(Evaluation.created_at <= end_date)

    if sort_dir not in {'asc', 'desc'}:
        return jsonify({'error': 'Invalid sort_dir. Use "asc" or "desc".'}), 400

    if page < 1 or per_page < 1:
        return jsonify({'error': 'page and per_page must be >= 1'}), 400

    order_clause = Evaluation.created_at.asc() if sort_dir == 'asc' else Evaluation.created_at.desc()
    total = query.count()
    evaluations = (
        query.order_by(order_clause)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total_pages = (total + per_page - 1) // per_page if per_page else 0
    return jsonify({
        'items': [e.to_dict() for e in evaluations],
        'meta': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'sort_dir': sort_dir
        }
    }), 200

def get_evaluation(evaluation_id):
    logger.info(f"Fetching evaluation: {evaluation_id}")
    
    # Get user's active unit
    user_id = _get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Authentication required'}), 401
    user = User.query.get(user_id)
    if not user or not user.active_unit_id:
        return jsonify({'error': 'No active unit selected'}), 400
    
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    
    # Check if evaluation belongs to user's active unit
    if evaluation.unit_id != user.active_unit_id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify(evaluation.to_dict(include_listings=True)), 200

def update_evaluation(evaluation_id, data=None):
    logger.info(f"Updating evaluation: {evaluation_id}")
    
    # Get user's active unit
    user_id = _get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Authentication required'}), 401
    user = User.query.get(user_id)
    if not user or not user.active_unit_id:
        return jsonify({'error': 'No active unit selected'}), 400
    
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    
    # Check if evaluation belongs to user's active unit
    if evaluation.unit_id != user.active_unit_id:
        return jsonify({'error': 'Access denied'}), 403
    
    if data is None:
        data = request.get_json()
    
    try:
        normalized_purpose = normalize_purpose(data.get('purpose')) if 'purpose' in data else None
        normalized_property_type = normalize_property_type(data.get('property_type')) if 'property_type' in data else None
        normalized_classification = normalize_classification(data.get('classification')) if 'classification' in data else None
        evaluation.address = data.get('address', evaluation.address)
        evaluation.neighborhood = data.get('neighborhood', evaluation.neighborhood)
        evaluation.city = data.get('city', evaluation.city)
        evaluation.state = data.get('state', evaluation.state)
        evaluation.area = data.get('area', evaluation.area)
        evaluation.region_value_sqm = data.get('region_value_sqm', evaluation.region_value_sqm)
        evaluation.analysis_type = data.get('analysis_type', evaluation.analysis_type)
        evaluation.owner_name = data.get('owner_name', evaluation.owner_name)
        evaluation.appraiser_name = data.get('appraiser_name', evaluation.appraiser_name)
        evaluation.estimated_price = data.get('estimated_price', evaluation.estimated_price)
        # rounded_price is always server-calculated to keep rules consistent.
        evaluation.description = data.get('description', evaluation.description)
        if 'classification' in data:
            evaluation.classification = normalized_classification
        if 'purpose' in data:
            evaluation.purpose = normalized_purpose
        if 'property_type' in data:
            evaluation.property_type = normalized_property_type
        evaluation.bedrooms = data.get('bedrooms', evaluation.bedrooms)
        evaluation.bathrooms = data.get('bathrooms', evaluation.bathrooms)
        evaluation.parking_spaces = data.get('parking_spaces', evaluation.parking_spaces)
        evaluation.analyzed_properties_count = data.get('analyzed_properties_count', evaluation.analyzed_properties_count)
        evaluation.depreciation = data.get('depreciation', evaluation.depreciation)

        should_recalculate_metrics = any(field in data for field in ('area', 'depreciation', 'classification'))

        if should_recalculate_metrics and evaluation.base_listings:
            evaluation.recalculate_metrics()
        else:
            evaluation.recalculate_rounded_price()

        db.session.commit()
        logger.info(f"Evaluation {evaluation_id} updated successfully")
        return jsonify(evaluation.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating evaluation {evaluation_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def delete_evaluation(evaluation_id):
    logger.info(f"Deleting evaluation: {evaluation_id}")
    
    # Get user's active unit
    user_id = _get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Authentication required'}), 401
    user = User.query.get(user_id)
    if not user or not user.active_unit_id:
        return jsonify({'error': 'No active unit selected'}), 400
    
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    
    # Check if evaluation belongs to user's active unit
    if evaluation.unit_id != user.active_unit_id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        db.session.delete(evaluation)
        db.session.commit()
        logger.info(f"Evaluation {evaluation_id} deleted successfully")
        return jsonify({'message': 'Evaluation deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting evaluation {evaluation_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# --- BaseListing CRUD ---

def create_base_listing(evaluation_id, data=None):
    logger.info(f"Creating base listing for evaluation: {evaluation_id}")
    user, error = _get_current_user_with_active_unit()
    if error:
        return error

    evaluation, error = _get_evaluation_for_user_or_error(evaluation_id, user)
    if error:
        return error

    if data is None:
        data = request.get_json()
    
    try:
        collected_at_str = data.get('collected_at')
        collected_at = datetime.fromisoformat(collected_at_str) if collected_at_str else datetime.utcnow()

        purpose = normalize_purpose(data.get('purpose'))
        normalized_type = normalize_property_type(data.get('type'))
        new_listing = BaseListing(
            evaluation_id=evaluation_id,
            sample_number=data.get('sample_number'),
            address=data.get('address'),
            neighborhood=data.get('neighborhood'),
            city=data.get('city'),
            state=data.get('state'),
            link=data.get('link'),
            bedrooms=data.get('bedrooms', 0),
            bathrooms=data.get('bathrooms', 0),
            living_rooms=data.get('living_rooms', 0),
            parking_spaces=data.get('parking_spaces', 0),
            collected_at=collected_at,
            rent_value=data.get('rent_value'),
            condo_fee=data.get('condo_fee'),
            purpose=purpose,
            type=normalized_type,
            area=data.get('area'),
            is_active=data.get('is_active', True),
            deactivation_reason=data.get('deactivation_reason')
        )
        db.session.add(new_listing)

        evaluation.recalculate_metrics()

        db.session.commit()
        
        # Refresh evaluation from database after commit
        evaluation_refreshed = Evaluation.query.get(evaluation_id)
        publish_event(
            f"evaluation:{evaluation_id}",
            "listing_added",
            {
                "listing": new_listing.to_dict(),
                "evaluation": evaluation_refreshed.to_dict() if evaluation_refreshed else evaluation.to_dict()
            }
        )
        return jsonify(new_listing.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def get_base_listings(evaluation_id):
    user, error = _get_current_user_with_active_unit()
    if error:
        return error

    evaluation, error = _get_evaluation_for_user_or_error(evaluation_id, user)
    if error:
        return error

    listings = BaseListing.query.filter_by(evaluation_id=evaluation_id).all()
    return jsonify([l.to_dict() for l in listings]), 200

def get_base_listing(listing_id):
    user, error = _get_current_user_with_active_unit()
    if error:
        return error

    listing, error = _get_listing_for_user_or_error(listing_id, user)
    if error:
        return error

    return jsonify(listing.to_dict()), 200
def update_base_listing(listing_id, data=None):
    user, error = _get_current_user_with_active_unit()
    if error:
        return error

    listing, error = _get_listing_for_user_or_error(listing_id, user)
    if error:
        return error

    if data is None:
        data = request.get_json()
    
    try:
        normalized_purpose = normalize_purpose(data.get('purpose')) if 'purpose' in data else None
        normalized_type = normalize_property_type(data.get('type')) if 'type' in data else None
        listing.sample_number = data.get('sample_number', listing.sample_number)
        listing.address = data.get('address', listing.address)
        listing.neighborhood = data.get('neighborhood', listing.neighborhood)
        listing.city = data.get('city', listing.city)
        listing.state = data.get('state', listing.state)
        listing.link = data.get('link', listing.link)
        listing.bedrooms = data.get('bedrooms', listing.bedrooms)
        listing.bathrooms = data.get('bathrooms', listing.bathrooms)
        listing.living_rooms = data.get('living_rooms', listing.living_rooms)
        listing.parking_spaces = data.get('parking_spaces', listing.parking_spaces)
        
        collected_at_str = data.get('collected_at')
        if collected_at_str:
             listing.collected_at = datetime.fromisoformat(collected_at_str)

        listing.rent_value = data.get('rent_value', listing.rent_value)
        listing.condo_fee = data.get('condo_fee', listing.condo_fee)
        if 'purpose' in data:
            listing.purpose = normalized_purpose
        if 'type' in data:
            listing.type = normalized_type
        listing.area = data.get('area', listing.area)
        
        # Handle activation/deactivation
        if 'is_active' in data:
            listing.is_active = data.get('is_active')
        if 'deactivation_reason' in data:
            listing.deactivation_reason = data.get('deactivation_reason')
        
        if listing.evaluation:
            listing.evaluation.recalculate_metrics()

        db.session.commit()
        
        # Refresh evaluation from database after commit
        evaluation_refreshed = Evaluation.query.get(listing.evaluation_id) if listing.evaluation_id else None
        if evaluation_refreshed:
            publish_event(
                f"evaluation:{listing.evaluation_id}",
                "listing_updated",
                {
                    "listing": listing.to_dict(),
                    "evaluation": evaluation_refreshed.to_dict()
                }
            )
        
        return jsonify(listing.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


def update_base_listings_bulk(evaluation_id, data=None):
    """
    Bulk update listing activation states for one evaluation.
    - persist=True: writes changes to DB and emits SSE event.
    - persist=False: returns preview-only metrics and listing states.
    """
    logger.info(f"Bulk updating base listings for evaluation: {evaluation_id}")

    user, error = _get_current_user_with_active_unit()
    if error:
        return error

    evaluation, error = _get_evaluation_for_user_or_error(evaluation_id, user)
    if error:
        return error

    if data is None:
        data = request.get_json(silent=True) or {}

    if not isinstance(data, dict):
        return jsonify({'error': 'Request body must be a JSON object'}), 400

    updates = data.get('updates')
    if updates is None:
        # Backward compatibility with previous frontend payload keys.
        legacy_updates = data.get('listings')
        if legacy_updates is None:
            legacy_updates = data.get('base_listings')
        if isinstance(legacy_updates, list):
            updates = legacy_updates

    persist = data.get('persist')
    if persist is None:
        persist_arg = request.args.get('persist')
        if persist_arg is None:
            persist = True
        else:
            normalized_persist = str(persist_arg).strip().lower()
            if normalized_persist in ('true', '1', 'yes', 'on'):
                persist = True
            elif normalized_persist in ('false', '0', 'no', 'off'):
                persist = False
            else:
                return jsonify({'error': 'persist must be a boolean'}), 400

    if not isinstance(persist, bool):
        return jsonify({'error': 'persist must be a boolean'}), 400

    if not isinstance(updates, list) or len(updates) == 0:
        return jsonify({'error': 'updates must be a non-empty list'}), 400

    listings_by_id = {listing.id: listing for listing in evaluation.base_listings}
    state_map = _build_listing_state_map(evaluation)
    touched_listing_ids = []

    for update in updates:
        if not isinstance(update, dict):
            return jsonify({'error': 'Each update must be an object'}), 400

        listing_id = update.get('id')
        if isinstance(listing_id, str) and listing_id.isdigit():
            listing_id = int(listing_id)

        if not isinstance(listing_id, int):
            return jsonify({'error': 'Each update must include integer field id'}), 400

        if listing_id not in listings_by_id:
            return jsonify({'error': f'Listing {listing_id} does not belong to evaluation {evaluation_id}'}), 404

        if 'is_active' in update and not isinstance(update.get('is_active'), bool):
            return jsonify({'error': f'is_active for listing {listing_id} must be a boolean'}), 400

        if listing_id not in touched_listing_ids:
            touched_listing_ids.append(listing_id)

        current_state = state_map[listing_id]
        if 'is_active' in update:
            current_state['is_active'] = update.get('is_active')
        if 'deactivation_reason' in update:
            current_state['deactivation_reason'] = update.get('deactivation_reason')

        if persist:
            listing = listings_by_id[listing_id]
            if 'is_active' in update:
                listing.is_active = update.get('is_active')
            if 'deactivation_reason' in update:
                listing.deactivation_reason = update.get('deactivation_reason')

    try:
        if persist:
            evaluation.recalculate_metrics()
            db.session.commit()

            refreshed_evaluation = Evaluation.query.get(evaluation_id)
            payload = {
                'persisted': True,
                'updated_listings': [listings_by_id[listing_id].to_dict() for listing_id in touched_listing_ids],
                'evaluation': refreshed_evaluation.to_dict() if refreshed_evaluation else evaluation.to_dict()
            }

            publish_event(
                f"evaluation:{evaluation_id}",
                "listings_bulk_updated",
                payload
            )
            return jsonify(payload), 200

        evaluation_preview = evaluation.to_dict()
        evaluation_preview.update(_calculate_evaluation_metrics_for_states(evaluation, state_map))

        preview_listings = []
        for listing_id in touched_listing_ids:
            listing_dict = listings_by_id[listing_id].to_dict()
            listing_dict['is_active'] = state_map[listing_id]['is_active']
            listing_dict['deactivation_reason'] = state_map[listing_id]['deactivation_reason']
            preview_listings.append(listing_dict)

        return jsonify({
            'persisted': False,
            'updated_listings': preview_listings,
            'evaluation': evaluation_preview
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def delete_base_listing(listing_id):
    user, error = _get_current_user_with_active_unit()
    if error:
        return error

    listing, error = _get_listing_for_user_or_error(listing_id, user)
    if error:
        return error

    try:
        evaluation = listing.evaluation
        db.session.delete(listing)
        db.session.flush()
        
        if evaluation:
            evaluation.recalculate_metrics()
            
        db.session.commit()
        return jsonify({'message': 'Base listing deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
