"""
Migration script to add whatsapp, address, and cnpj fields to units table.
Run this script to add the new fields to existing units.
"""

import sys
import os

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

def add_unit_fields():
    """Add whatsapp, address, and cnpj columns to units table."""
    app = create_app()
    
    with app.app_context():
        try:
            print("Adding new fields to units table...")
            
            # Add whatsapp column
            db.session.execute(text("""
                ALTER TABLE units 
                ADD COLUMN IF NOT EXISTS whatsapp VARCHAR(20);
            """))
            print("✓ Added whatsapp column")
            
            # Add address column
            db.session.execute(text("""
                ALTER TABLE units 
                ADD COLUMN IF NOT EXISTS address VARCHAR(255);
            """))
            print("✓ Added address column")
            
            # Add cnpj column
            db.session.execute(text("""
                ALTER TABLE units 
                ADD COLUMN IF NOT EXISTS cnpj VARCHAR(18);
            """))
            print("✓ Added cnpj column")
            
            db.session.commit()
            print("\n✅ Migration completed successfully!")
            print("\nNew fields added:")
            print("  - whatsapp (VARCHAR(20))")
            print("  - address (VARCHAR(255))")
            print("  - cnpj (VARCHAR(18))")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during migration: {str(e)}")
            return False
        
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("Unit Fields Migration Script")
    print("=" * 60)
    print("\nThis script will add the following fields to the units table:")
    print("  - whatsapp (for WhatsApp contact)")
    print("  - address (for unit address)")
    print("  - cnpj (for Brazilian tax ID)")
    print("\nAll fields are optional (nullable).")
    print("=" * 60)
    
    response = input("\nDo you want to proceed? (yes/no): ").strip().lower()
    
    if response == 'yes':
        success = add_unit_fields()
        sys.exit(0 if success else 1)
    else:
        print("\n❌ Migration cancelled by user.")
        sys.exit(0)
