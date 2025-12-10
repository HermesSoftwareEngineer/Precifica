from app.models.user import User
from app.extensions import db, bcrypt
import logging

logger = logging.getLogger(__name__)

def get_all_users():
    logger.info("Fetching all users")
    return User.query.all()

def get_user_by_id(user_id):
    logger.info(f"Fetching user with ID: {user_id}")
    return User.query.get_or_404(user_id)

def create_user_admin(username, email, password, is_admin=False):
    logger.info(f"Creating admin user: {username}, email: {email}, is_admin: {is_admin}")
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(username=username, email=email, password=hashed_password, is_admin=is_admin)
    db.session.add(user)
    db.session.commit()
    logger.info(f"User created successfully: {user.id}")
    return user

def update_user_admin(user, username, email, is_admin):
    logger.info(f"Updating user {user.id}: username={username}, email={email}, is_admin={is_admin}")
    user.username = username
    user.email = email
    user.is_admin = is_admin
    db.session.commit()
    logger.info(f"User {user.id} updated successfully")
    return user

def delete_user_admin(user):
    logger.info(f"Deleting user {user.id}")
    db.session.delete(user)
    db.session.commit()
    logger.info(f"User {user.id} deleted successfully")
