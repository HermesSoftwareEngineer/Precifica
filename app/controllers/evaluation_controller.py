from flask import jsonify, request
from app.models.evaluation import Evaluation, BaseListing
from app.extensions import db
from datetime import datetime

# --- Evaluation CRUD ---

def create_evaluation():
    data = request.get_json()
    try:
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
            purpose=data.get('purpose'),
            property_type=data.get('property_type'),
            bedrooms=data.get('bedrooms', 0),
            bathrooms=data.get('bathrooms', 0),
            parking_spaces=data.get('parking_spaces', 0),
            analyzed_properties_count=data.get('analyzed_properties_count', 0)
        )
        db.session.add(new_evaluation)
        db.session.commit()
        return jsonify(new_evaluation.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def get_evaluations():
    evaluations = Evaluation.query.all()
    return jsonify([e.to_dict() for e in evaluations]), 200

def get_evaluation(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    return jsonify(evaluation.to_dict(include_listings=True)), 200

def update_evaluation(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    data = request.get_json()
    
    try:
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
        evaluation.purpose = data.get('purpose', evaluation.purpose)
        evaluation.property_type = data.get('property_type', evaluation.property_type)
        evaluation.bedrooms = data.get('bedrooms', evaluation.bedrooms)
        evaluation.bathrooms = data.get('bathrooms', evaluation.bathrooms)
        evaluation.parking_spaces = data.get('parking_spaces', evaluation.parking_spaces)
        evaluation.analyzed_properties_count = data.get('analyzed_properties_count', evaluation.analyzed_properties_count)
        
        if 'area' in data:
            evaluation.recalculate_metrics()

        db.session.commit()
        return jsonify(evaluation.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

def delete_evaluation(evaluation_id):
    evaluation = Evaluation.query.get_or_404(evaluation_id)
    try:
        db.session.delete(evaluation)
        db.session.commit()
        return jsonify({'message': 'Evaluation deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# --- BaseListing CRUD ---

def create_base_listing(evaluation_id):
    # Ensure evaluation exists
    Evaluation.query.get_or_404(evaluation_id)
    data = request.get_json()
    
    try:
        collected_at_str = data.get('collected_at')
        collected_at = datetime.fromisoformat(collected_at_str) if collected_at_str else datetime.utcnow()

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
            purpose=data.get('purpose'),
            type=data.get('type'),
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

def update_base_listing(listing_id):
    listing = BaseListing.query.get_or_404(listing_id)
    data = request.get_json()
    
    try:
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
        listing.purpose = data.get('purpose', listing.purpose)
        listing.type = data.get('type', listing.type)
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
