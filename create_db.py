from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models.user import User
from app.models.chat import Conversation, Message
from app.models.evaluation import Evaluation, BaseListing

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created.")
