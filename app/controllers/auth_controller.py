from app.models.user import User
from app.extensions import db, bcrypt
from flask_login import login_user, logout_user

def register_user(username, email, password):
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return user

def login_user_by_email(email, password, remember=False):
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        login_user(user, remember=remember)
        return True
    return False

def logout():
    logout_user()
