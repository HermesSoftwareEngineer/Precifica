from app.models.user import User
from app.extensions import db, bcrypt

def get_all_users():
    return User.query.all()

def get_user_by_id(user_id):
    return User.query.get_or_404(user_id)

def create_user_admin(username, email, password, is_admin=False):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, email=email, password=hashed_password, is_admin=is_admin)
    db.session.add(user)
    db.session.commit()
    return user

def update_user_admin(user, username, email, is_admin):
    user.username = username
    user.email = email
    user.is_admin = is_admin
    db.session.commit()
    return user

def delete_user_admin(user):
    db.session.delete(user)
    db.session.commit()
