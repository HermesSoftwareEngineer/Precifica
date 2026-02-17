"""
Direct SQL migration script for Units feature.
This bypasses ORM issues by executing raw SQL.
"""

import sys
from app import create_app, db
from sqlalchemy import text, inspect

def table_exists(table_name):
    """Check if a table exists."""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    return any(col['name'] == column_name for col in columns)

def migrate():
    app = create_app()
    with app.app_context():
        print("Starting direct SQL migration for Units feature...\n")
        
        try:
            # 1. Create units table if it doesn't exist
            print("1. Checking 'units' table...")
            if not table_exists('units'):
                print("   - Creating 'units' table...")
                db.session.execute(text("""
                    CREATE TABLE units (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(150) NOT NULL,
                        email VARCHAR(120),
                        phone VARCHAR(20),
                        logo_url VARCHAR(255),
                        custom_fields JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.session.commit()
                print("   ✓ 'units' table created")
            else:
                print("   ✓ 'units' table already exists")
            
            # 2. Create user_units table if it doesn't exist
            print("\n2. Checking 'user_units' table...")
            if not table_exists('user_units'):
                print("   - Creating 'user_units' table...")
                db.session.execute(text("""
                    CREATE TABLE user_units (
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        unit_id INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
                        role VARCHAR(50) DEFAULT 'member',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, unit_id)
                    )
                """))
                db.session.commit()
                print("   ✓ 'user_units' table created")
            else:
                print("   ✓ 'user_units' table already exists")
            
            # 3. Create default unit if it doesn't exist
            print("\n3. Creating default unit...")
            result = db.session.execute(text("""
                SELECT id FROM units WHERE name = 'Default Unit' LIMIT 1
            """))
            default_unit = result.fetchone()
            
            if not default_unit:
                print("   - Inserting default unit...")
                db.session.execute(text("""
                    INSERT INTO units (name, email, custom_fields) 
                    VALUES ('Default Unit', 'admin@default.com', '{}')
                """))
                db.session.commit()
                # Get the ID
                result = db.session.execute(text("""
                    SELECT id FROM units WHERE name = 'Default Unit'
                """))
                default_unit = result.fetchone()
                default_unit_id = default_unit[0]
                print(f"   ✓ Default unit created with ID: {default_unit_id}")
            else:
                default_unit_id = default_unit[0]
                print(f"   ✓ Default unit already exists with ID: {default_unit_id}")
            
            # 4. Add active_unit_id to users table
            print("\n4. Checking 'users.active_unit_id' column...")
            if not column_exists('users', 'active_unit_id'):
                print("   - Adding 'active_unit_id' column to 'users' table...")
                db.session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN active_unit_id INTEGER REFERENCES units(id)
                """))
                # Set default value for existing users
                db.session.execute(text(f"""
                    UPDATE users SET active_unit_id = {default_unit_id}
                """))
                db.session.commit()
                print("   ✓ 'active_unit_id' column added to 'users' table")
                
                # Associate all users with default unit
                print("   - Associating users with default unit...")
                db.session.execute(text(f"""
                    INSERT INTO user_units (user_id, unit_id, role)
                    SELECT users.id, {default_unit_id}, 'member'
                    FROM users
                    WHERE NOT EXISTS (
                        SELECT 1 FROM user_units 
                        WHERE user_units.user_id = users.id
                        AND user_units.unit_id = {default_unit_id}
                    )
                """))
                db.session.commit()
                print("   ✓ Users associated with default unit")
            else:
                print("   ✓ 'active_unit_id' column already exists")
            
            # 5. Add unit_id to evaluations table
            print("\n5. Checking 'evaluations.unit_id' column...")
            if not column_exists('evaluations', 'unit_id'):
                print("   - Adding 'unit_id' column to 'evaluations' table...")
                
                # Check if table exists before modifying
                if table_exists('evaluations'):
                    # Add nullable column first
                    db.session.execute(text("""
                        ALTER TABLE evaluations 
                        ADD COLUMN unit_id INTEGER
                    """))
                    db.session.commit()
                    
                    # Update existing rows with default unit
                    db.session.execute(text(f"""
                        UPDATE evaluations 
                        SET unit_id = {default_unit_id}
                        WHERE unit_id IS NULL
                    """))
                    db.session.commit()
                    
                    # Add foreign key constraint
                    db.session.execute(text("""
                        ALTER TABLE evaluations 
                        ADD CONSTRAINT fk_evaluations_unit_id 
                        FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
                    """))
                    db.session.commit()
                    
                    # Make column NOT NULL
                    db.session.execute(text("""
                        ALTER TABLE evaluations 
                        ALTER COLUMN unit_id SET NOT NULL
                    """))
                    db.session.commit()
                    print("   ✓ 'unit_id' column added to 'evaluations' table")
                else:
                    print("   - 'evaluations' table doesn't exist, skipping")
            else:
                print("   ✓ 'unit_id' column already exists")
            
            # 6. Add unit_id to conversations table
            print("\n6. Checking 'conversations.unit_id' column...")
            if not column_exists('conversations', 'unit_id'):
                print("   - Adding 'unit_id' column to 'conversations' table...")
                
                # Check if table exists before modifying
                if table_exists('conversations'):
                    # Add nullable column first
                    db.session.execute(text("""
                        ALTER TABLE conversations 
                        ADD COLUMN unit_id INTEGER
                    """))
                    db.session.commit()
                    
                    # Update existing rows with default unit
                    db.session.execute(text(f"""
                        UPDATE conversations 
                        SET unit_id = {default_unit_id}
                        WHERE unit_id IS NULL
                    """))
                    db.session.commit()
                    
                    # Add foreign key constraint
                    db.session.execute(text("""
                        ALTER TABLE conversations 
                        ADD CONSTRAINT fk_conversations_unit_id 
                        FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
                    """))
                    db.session.commit()
                    
                    # Make column NOT NULL
                    db.session.execute(text("""
                        ALTER TABLE conversations 
                        ALTER COLUMN unit_id SET NOT NULL
                    """))
                    db.session.commit()
                    print("   ✓ 'unit_id' column added to 'conversations' table")
                else:
                    print("   - 'conversations' table doesn't exist, skipping")
            else:
                print("   ✓ 'unit_id' column already exists")
            
            print("\n✅ Migration completed successfully!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during migration: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)

