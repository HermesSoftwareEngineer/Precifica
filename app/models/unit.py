from app.extensions import db
from datetime import datetime
from sqlalchemy import event
import json

# Association table for M2M relationship between User and Unit
user_units = db.Table(
    'user_units',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('unit_id', db.Integer, db.ForeignKey('units.id'), primary_key=True),
    db.Column('role', db.String(50), default='member'),  # 'admin', 'manager', 'member'
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class Unit(db.Model):
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    cnpj = db.Column(db.String(18), nullable=True)  # Format: 00.000.000/0000-00
    logo_url = db.Column(db.String(255), nullable=True)
    
    # Custom fields as JSON
    custom_fields = db.Column(db.JSON, nullable=True, default={})
    
    # Relationship with users
    users = db.relationship(
        'User',
        secondary=user_units,
        backref=db.backref('units', lazy='dynamic'),
        lazy='dynamic'
    )
    
    # Relationship with evaluations
    evaluations = db.relationship('Evaluation', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
    
    # Relationship with conversations
    conversations = db.relationship('Conversation', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def add_user(self, user, role='member'):
        """Add a user to the unit with a specific role."""
        from sqlalchemy import text
        
        # Check if user is already in the unit
        existing = self.users.filter_by(id=user.id).first()
        
        if not existing:
            # Add new user
            db.session.execute(text("""
                INSERT INTO user_units (user_id, unit_id, role, created_at)
                VALUES (:user_id, :unit_id, :role, CURRENT_TIMESTAMP)
            """), {'user_id': user.id, 'unit_id': self.id, 'role': role})
        else:
            # Update role if user already exists
            db.session.execute(text("""
                UPDATE user_units 
                SET role = :role
                WHERE user_id = :user_id AND unit_id = :unit_id
            """), {'user_id': user.id, 'unit_id': self.id, 'role': role})
    
    def remove_user(self, user):
        """Remove a user from the unit. Prevents removal of global admins."""
        # Prevent removal of global admins
        if user.is_admin:
            raise ValueError(f"Cannot remove global admin '{user.username}' from unit")
        
        if self.users.filter_by(id=user.id).first():
            self.users.remove(user)
    
    def get_user_role(self, user):
        """Get the role of a user in this unit."""
        result = db.session.query(user_units.c.role).filter(
            user_units.c.user_id == user.id,
            user_units.c.unit_id == self.id
        ).first()
        return result[0] if result else None
    
    def is_user_admin(self, user):
        """Check if user is admin in this unit."""
        role = self.get_user_role(user)
        return role in ['admin', 'manager']
    
    def to_dict(self, include_users=False):
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'whatsapp': self.whatsapp,
            'address': self.address,
            'cnpj': self.cnpj,
            'logo_url': self.logo_url,
            'custom_fields': self.custom_fields or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_users:
            data['users'] = [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': self.get_user_role(user)
                }
                for user in self.users
            ]
        
        return data
    
    def __repr__(self):
        return f"Unit('{self.name}')"

# Event listener to auto-add global admins to new units
@event.listens_for(Unit, 'after_insert')
def add_global_admins_to_unit(mapper, connection, target):
    """
    Automatically add all global admins to newly created units.
    This ensures super admins always have access to all units.
    """
    from sqlalchemy import text
    
    # Get all global admins
    result = connection.execute(text("""
        SELECT id FROM users WHERE is_admin = true
    """))
    
    admin_ids = [row[0] for row in result]
    
    # Add each admin to the new unit
    for admin_id in admin_ids:
        # Check if already exists (shouldn't, but just in case)
        exists = connection.execute(text("""
            SELECT 1 FROM user_units 
            WHERE user_id = :user_id AND unit_id = :unit_id
        """), {'user_id': admin_id, 'unit_id': target.id}).fetchone()
        
        if not exists:
            connection.execute(text("""
                INSERT INTO user_units (user_id, unit_id, role, created_at)
                VALUES (:user_id, :unit_id, 'admin', CURRENT_TIMESTAMP)
            """), {'user_id': admin_id, 'unit_id': target.id})
