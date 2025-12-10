from app.models.user import User
from app.extensions import db, bcrypt
from flask_jwt_extended import create_access_token
import logging

logger = logging.getLogger(__name__)

def register_user(username, email, password):
    logger.info(f"Registering user: {username}, email: {email}")
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, email=email, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    logger.info(f"User registered successfully: {user.id}")
    return user

def login_user_by_email(email, password):
    logger.info(f"Attempting login for email: {email}")
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.id))
        logger.info(f"Login successful for user: {user.id}")
        return access_token, user
    logger.warning(f"Login failed for email: {email}")
    return None, None

def logout():
    logger.info("Logging out user")
    # Client side should discard the token
    pass
