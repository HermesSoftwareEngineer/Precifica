from app.models.user import User
from app.extensions import db, bcrypt
from flask_login import login_user, logout_user
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

def login_user_by_email(email, password, remember=False):
    logger.info(f"Attempting login for email: {email}")
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        login_user(user, remember=remember)
        logger.info(f"Login successful for user: {user.id}")
        return True
    logger.warning(f"Login failed for email: {email}")
    return False

def logout():
    logger.info("Logging out user")
    logout_user()
