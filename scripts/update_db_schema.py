
from dotenv import load_dotenv
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as connection:
        try:
            # Check if column exists using information_schema (standard SQL)
            result = connection.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='conversations' AND column_name='evaluation_id'"
            ))
            if result.rowcount == 0:
                print("Adding evaluation_id column to conversations table...")
                connection.execute(text("ALTER TABLE conversations ADD COLUMN evaluation_id INTEGER REFERENCES evaluations(id)"))
                connection.commit()
                print("Column added successfully.")
            else:
                print("Column evaluation_id already exists.")
                
        except Exception as e:
            print(f"An error occurred: {e}")
