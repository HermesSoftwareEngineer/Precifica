"""
Quick fix script to add created_at and updated_at to units that don't have them.
"""

import sys
from app import create_app, db
from sqlalchemy import text
from datetime import datetime

def fix_unit_dates():
    app = create_app()
    with app.app_context():
        print("Fixing unit dates...\n")
        
        try:
            # Update units that have NULL created_at or updated_at
            result = db.session.execute(text("""
                UPDATE units 
                SET created_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE created_at IS NULL OR updated_at IS NULL
                RETURNING id, name
            """))
            
            updated = result.fetchall()
            
            if updated:
                print(f"✓ Updated {len(updated)} unit(s):")
                for unit_id, name in updated:
                    print(f"  - Unit {unit_id}: {name}")
            else:
                print("✓ All units already have dates set")
            
            db.session.commit()
            print("\n✅ Fix completed successfully!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = fix_unit_dates()
    sys.exit(0 if success else 1)
