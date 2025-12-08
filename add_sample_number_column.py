from dotenv import load_dotenv
load_dotenv()

from app import create_app, db

app = create_app()

with app.app_context():
    # Execute raw SQL to add the column
    try:
        db.session.execute(db.text("ALTER TABLE base_listings ADD COLUMN IF NOT EXISTS sample_number INTEGER;"))
        db.session.commit()
        print("Column 'sample_number' added successfully to 'base_listings' table.")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding column: {e}")
