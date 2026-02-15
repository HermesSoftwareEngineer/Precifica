from flask import jsonify, request
from app.models.evaluation import Evaluation, BaseListing
from app.extensions import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

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

# --- Evaluation CRUD ---

def create_evaluation(data=None):
    logger.info("Creating new evaluation")
    if data is None:
        data = request.get_json()
    try:
        purpose = normalize_purpose(data.get('purpose'))
        property_type = normalize_property_type(data.get('property_type'))
        new_evaluation = Evaluation(
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
            rounded_price=data.get('rounded_price'),
            description=data.get('description'),
            classification=data.get('classification'),
            purpose=purpose,
            property_type=property_type,
            bedrooms=data.get('bedrooms', 0),
            bathrooms=data.get('bathrooms', 0),
            parking_spaces=data.get('parking_spaces', 0),
            analyzed_properties_count=data.get('analyzed_properties_count', 0)
        )
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
    query = Evaluation.query
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
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    return jsonify(evaluation.to_dict(include_listings=True)), 200

def update_evaluation(evaluation_id, data=None):
    logger.info(f"Updating evaluation: {evaluation_id}")
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    if data is None:
        data = request.get_json()
    
    try:
        normalized_purpose = normalize_purpose(data.get('purpose')) if 'purpose' in data else None
        normalized_property_type = normalize_property_type(data.get('property_type')) if 'property_type' in data else None
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
        evaluation.rounded_price = data.get('rounded_price', evaluation.rounded_price)
        evaluation.description = data.get('description', evaluation.description)
        evaluation.classification = data.get('classification', evaluation.classification)
        if 'purpose' in data:
            evaluation.purpose = normalized_purpose
        if 'property_type' in data:
            evaluation.property_type = normalized_property_type
        evaluation.bedrooms = data.get('bedrooms', evaluation.bedrooms)
        evaluation.bathrooms = data.get('bathrooms', evaluation.bathrooms)
        evaluation.parking_spaces = data.get('parking_spaces', evaluation.parking_spaces)
        evaluation.analyzed_properties_count = data.get('analyzed_properties_count', evaluation.analyzed_properties_count)
        
        if 'area' in data:
            evaluation.recalculate_metrics()

        db.session.commit()
        logger.info(f"Evaluation {evaluation_id} updated successfully")
        return jsonify(evaluation.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating evaluation {evaluation_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def delete_evaluation(evaluation_id):
    logger.info(f"Deleting evaluation: {evaluation_id}")
    evaluation = Evaluation.query.get_or_404(evaluation_id)
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
    # Ensure evaluation exists
    Evaluation.query.get_or_404(evaluation_id)
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
            area=data.get('area')
        )
        db.session.add(new_listing)
        db.session.flush()
        
        evaluation = Evaluation.query.get(evaluation_id)
        if evaluation:
            evaluation.recalculate_metrics()

        db.session.commit()
        return jsonify(new_listing.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def get_base_listings(evaluation_id):
    Evaluation.query.get_or_404(evaluation_id)
    listings = BaseListing.query.filter_by(evaluation_id=evaluation_id).all()
    return jsonify([l.to_dict() for l in listings]), 200

def get_base_listing(listing_id):
    listing = BaseListing.query.get_or_404(listing_id)
    return jsonify(listing.to_dict()), 200
def update_base_listing(listing_id, data=None):
    listing = BaseListing.query.get_or_404(listing_id)
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
        
        if listing.evaluation:
            listing.evaluation.recalculate_metrics()

        db.session.commit()
        return jsonify(listing.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def delete_base_listing(listing_id):
    listing = BaseListing.query.get_or_404(listing_id)
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
