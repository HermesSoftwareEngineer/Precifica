from app.extensions import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)  # Aumentado de 20 para 100
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    active_unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    
    # Relationship with active unit
    active_unit = db.relationship('Unit', foreign_keys=[active_unit_id], backref='active_users')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'active_unit_id': self.active_unit_id
        }

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
