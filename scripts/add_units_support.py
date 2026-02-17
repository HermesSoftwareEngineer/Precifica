"""
Migration script to add Units support to the database.
This script:
1. Creates the units table
2. Creates the user_units association table (M2M)
3. Adds unit_id column to evaluations and conversations
4. Adds active_unit_id column to users
5. Creates a default unit
6. Associates all existing users with the default unit
"""

import sys
from app import create_app, db
from app.models import Unit, User, Evaluation, Conversation

def migrate():
    app = create_app()
    with app.app_context():
        print("Starting migration...")
        
        try:
            # Create Unit table if it doesn't exist
            print("Creating units table...")
            db.create_all()
            
            # Create a default unit
            print("Creating default unit...")
            default_unit = db.session.query(Unit).filter_by(name='Default Unit').first()
            if not default_unit:
                default_unit = Unit(
                    name='Default Unit',
                    email='admin@defaultunit.com',
                    phone=None,
                    custom_fields={}
                )
                db.session.add(default_unit)
                db.session.commit()
                print(f"Default unit created with ID: {default_unit.id}")
            else:
                print(f"Default unit already exists with ID: {default_unit.id}")
            
            # Associate all existing users with the default unit
            print("Associating existing users with default unit...")
            users = db.session.query(User).all()
            for user in users:
                if not user.units.filter_by(id=default_unit.id).first():
                    default_unit.users.append(user)
                    if not user.active_unit_id:
                        user.active_unit_id = default_unit.id
                    print(f"Associated user {user.username} with default unit")
            
            # Update all existing evaluations to belong to default unit
            print("Associating existing evaluations with default unit...")
            evaluations = db.session.query(Evaluation).all()
            for evaluation in evaluations:
                if not evaluation.unit_id:
                    evaluation.unit_id = default_unit.id
                    print(f"Associated evaluation {evaluation.id} with default unit")
            
            # Update all existing conversations to belong to default unit
            print("Associating existing conversations with default unit...")
            conversations = db.session.query(Conversation).all()
            for conversation in conversations:
                if not conversation.unit_id:
                    conversation.unit_id = default_unit.id
                    print(f"Associated conversation {conversation.id} with default unit")
            
            # Commit all changes
            db.session.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during migration: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    migrate()
