"""
Script to promote a user to Super Admin.
Super Admins:
- Have is_admin = True (global admin)
- Have access to ALL units automatically
- Cannot be removed from units
- Are automatically added to new units
"""

import sys
from app import create_app, db
from app.models import User, Unit
from sqlalchemy import text

def promote_to_super_admin(email):
    """Promote a user to Super Admin status."""
    app = create_app()
    with app.app_context():
        print(f"Looking for user with email: {email}...")
        
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"❌ User with email {email} not found!")
            return False
        
        print(f"✓ Found user: {user.username} (ID: {user.id})")
        
        try:
            # 1. Set as global admin
            if not user.is_admin:
                user.is_admin = True
                print("   - Set is_admin = True")
            else:
                print("   ✓ Already is_admin = True")
            
            # 2. Get all units
            all_units = Unit.query.all()
            print(f"\n   Found {len(all_units)} unit(s) in the system")
            
            # 3. Add user to all units as 'admin' role
            for unit in all_units:
                # Check if user is already in the unit
                if not user.units.filter_by(id=unit.id).first():
                    # Add user to unit
                    db.session.execute(text("""
                        INSERT INTO user_units (user_id, unit_id, role)
                        VALUES (:user_id, :unit_id, 'admin')
                    """), {'user_id': user.id, 'unit_id': unit.id})
                    print(f"   - Added to unit '{unit.name}' as admin")
                else:
                    # Update role to admin if not already
                    db.session.execute(text("""
                        UPDATE user_units 
                        SET role = 'admin'
                        WHERE user_id = :user_id AND unit_id = :unit_id
                    """), {'user_id': user.id, 'unit_id': unit.id})
                    print(f"   ✓ Already in unit '{unit.name}', role updated to admin")
            
            # 4. Set active unit if not set
            if not user.active_unit_id and all_units:
                user.active_unit_id = all_units[0].id
                print(f"\n   - Set active_unit_id to {all_units[0].name}")
            
            db.session.commit()
            
            print(f"\n✅ User {user.username} is now a Super Admin!")
            print(f"   - Global admin: {user.is_admin}")
            print(f"   - Access to {len(all_units)} unit(s)")
            print(f"   - Active unit: {user.active_unit.name if user.active_unit else 'None'}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    # Super admin email - this user will have access to all units
    SUPER_ADMIN_EMAIL = 'hermesbarbosa9@gmail.com'
    
    success = promote_to_super_admin(SUPER_ADMIN_EMAIL)
    sys.exit(0 if success else 1)
