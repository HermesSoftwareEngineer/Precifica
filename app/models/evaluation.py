from app.extensions import db
from datetime import datetime

class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    neighborhood = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    area = db.Column(db.Float, nullable=False)
    region_value_sqm = db.Column(db.Float, nullable=True)
    analysis_type = db.Column(db.String(50), nullable=False) # 'region' or 'street'
    owner_name = db.Column(db.String(100), nullable=True)
    appraiser_name = db.Column(db.String(100), nullable=True)
    estimated_price = db.Column(db.Float, nullable=True)
    rounded_price = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    classification = db.Column(db.String(50), nullable=True) # Rent or Sale
    purpose = db.Column(db.String(50), nullable=True) # Residential or Commercial
    property_type = db.Column(db.String(50), nullable=True) # Apartment, House, etc.
    bedrooms = db.Column(db.Integer, default=0)
    bathrooms = db.Column(db.Integer, default=0)
    parking_spaces = db.Column(db.Integer, default=0)
    analyzed_properties_count = db.Column(db.Integer, default=0)
    depreciation = db.Column(db.Float, default=0.0, nullable=False)  # Percentage (0-100)
    last_chat_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with BaseListing
    base_listings = db.relationship('BaseListing', backref='evaluation', lazy=True, cascade="all, delete-orphan")

    # Relationship with Conversation
    conversations = db.relationship('Conversation', backref='evaluation', lazy=True, cascade="all, delete-orphan")

    def recalculate_metrics(self):
        """
        Recalculates region_value_sqm, estimated_price, rounded_price, and analyzed_properties_count
        based on the associated base_listings.
        """
        # Only consider active listings
        listings = [listing for listing in self.base_listings if listing.is_active]
        self.analyzed_properties_count = len(listings)
        
        if not listings:
            self.region_value_sqm = 0.0
            self.estimated_price = 0.0
            self.rounded_price = 0.0
            return

        total_sqm_value = 0.0
        valid_listings_count = 0

        for listing in listings:
            if listing.rent_value and listing.area and listing.area > 0:
                sqm_value = listing.rent_value / listing.area
                total_sqm_value += sqm_value
                valid_listings_count += 1
        
        if valid_listings_count > 0:
            self.region_value_sqm = total_sqm_value / valid_listings_count
        else:
            self.region_value_sqm = 0.0
            
        if self.area:
            self.estimated_price = self.area * self.region_value_sqm
            
            # Apply depreciation to estimated price before rounding
            price_after_depreciation = self.estimated_price
            if self.depreciation and self.depreciation > 0:
                price_after_depreciation = self.estimated_price * (1 - self.depreciation / 100)
            
            classification_lower = (self.classification or "").lower()
            if "venda" in classification_lower or "sale" in classification_lower:
                self.rounded_price = round(price_after_depreciation / 10000) * 10000
            else:
                self.rounded_price = round(price_after_depreciation / 10) * 10
        else:
            self.estimated_price = 0.0
            self.rounded_price = 0.0

    def get_active_listings_count(self):
        """Returns the count of active listings."""
        return sum(1 for listing in self.base_listings if listing.is_active)
    
    def get_inactive_listings_count(self):
        """Returns the count of inactive listings."""
        return sum(1 for listing in self.base_listings if not listing.is_active)
    
    def get_total_listings_count(self):
        """Returns the total count of all listings (active + inactive)."""
        return len(self.base_listings)

    def to_dict(self, include_listings=False):
        data = {
            'id': self.id,
            'unit_id': self.unit_id,
            'address': self.address,
            'neighborhood': self.neighborhood,
            'city': self.city,
            'state': self.state,
            'area': self.area,
            'region_value_sqm': self.region_value_sqm,
            'analysis_type': self.analysis_type,
            'owner_name': self.owner_name,
            'appraiser_name': self.appraiser_name,
            'estimated_price': self.estimated_price,
            'rounded_price': self.rounded_price,
            'description': self.description,
            'classification': self.classification,
            'purpose': self.purpose,
            'property_type': self.property_type,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'parking_spaces': self.parking_spaces,
            'analyzed_properties_count': self.analyzed_properties_count,
            'depreciation': self.depreciation,
            'active_listings_count': self.get_active_listings_count(),
            'inactive_listings_count': self.get_inactive_listings_count(),
            'total_listings_count': self.get_total_listings_count(),
            'last_chat_id': self.last_chat_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_listings:
            data['base_listings'] = [listing.to_dict() for listing in self.base_listings]
            
        return data

    def __repr__(self):
        return f"<Evaluation {self.id} - {self.address}>"


class BaseListing(db.Model):
    __tablename__ = 'base_listings'

    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'), nullable=False)
    sample_number = db.Column(db.Integer, nullable=True)
    
    address = db.Column(db.String(255), nullable=True)
    neighborhood = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    link = db.Column(db.String(500), nullable=True)
    bedrooms = db.Column(db.Integer, default=0)
    bathrooms = db.Column(db.Integer, default=0)
    living_rooms = db.Column(db.Integer, default=0)
    parking_spaces = db.Column(db.Integer, default=0)
    collected_at = db.Column(db.DateTime, default=datetime.utcnow)
    rent_value = db.Column(db.Float, nullable=True)
    condo_fee = db.Column(db.Float, nullable=True)
    purpose = db.Column(db.String(50), nullable=True) # Residential, Commercial
    type = db.Column(db.String(50), nullable=True) # Apartment, House, etc.
    area = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    deactivation_reason = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'evaluation_id': self.evaluation_id,
            'sample_number': self.sample_number,
            'address': self.address,
            'neighborhood': self.neighborhood,
            'city': self.city,
            'state': self.state,
            'link': self.link,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'living_rooms': self.living_rooms,
            'parking_spaces': self.parking_spaces,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'rent_value': self.rent_value,
            'condo_fee': self.condo_fee,
            'purpose': self.purpose,
            'type': self.type,
            'area': self.area,
            'is_active': self.is_active,
            'deactivation_reason': self.deactivation_reason
        }

    def __repr__(self):
        return f"<BaseListing {self.id} - {self.address}>"
