"""
Test script to verify super admin functionality:
1. Super admin has access to all units
2. New units automatically get super admin added
3. Super admin cannot be removed from units
"""

import sys
from app import create_app, db
from app.models import User, Unit

def test_super_admin():
    """Test super admin functionality."""
    app = create_app()
    with app.app_context():
        print("Testing Super Admin functionality...\n")
        
        # Get super admin
        super_admin = User.query.filter_by(email='hermesbarbosa9@gmail.com').first()
        if not super_admin:
            print("❌ Super admin not found!")
            return False
        
        print(f"✓ Super Admin: {super_admin.username}")
        print(f"  - is_admin: {super_admin.is_admin}")
        print(f"  - Units: {super_admin.units.count()}")
        
        # Test 1: Create a new unit
        print("\n1. Creating a new test unit...")
        test_unit = Unit(
            name='Test Unit - Auto Add Super Admin',
            email='test@unit.com'
        )
        db.session.add(test_unit)
        db.session.commit()
        print(f"   ✓ Created unit: {test_unit.name} (ID: {test_unit.id})")
        
        # Test 2: Check if super admin was auto-added
        print("\n2. Checking if super admin was auto-added...")
        is_in_unit = super_admin.units.filter_by(id=test_unit.id).first()
        if is_in_unit:
            role = test_unit.get_user_role(super_admin)
            print(f"   ✓ Super admin automatically added to new unit!")
            print(f"   ✓ Role: {role}")
        else:
            print(f"   ❌ Super admin NOT automatically added!")
            db.session.delete(test_unit)
            db.session.commit()
            return False
        
        # Test 3: Try to remove super admin (should fail)
        print("\n3. Testing protection against removal...")
        try:
            test_unit.remove_user(super_admin)
            db.session.commit()
            print("   ❌ Super admin was removed (should have been prevented!)")
            success = False
        except ValueError as e:
            print(f"   ✓ Removal prevented: {str(e)}")
            db.session.rollback()
            success = True
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
            db.session.rollback()
            success = False
        
        # Cleanup
        print("\n4. Cleaning up test unit...")
        db.session.delete(test_unit)
        db.session.commit()
        print("   ✓ Test unit deleted")
        
        if success:
            print("\n✅ All tests passed! Super admin functionality works correctly.")
        else:
            print("\n❌ Some tests failed.")
        
        return success

if __name__ == '__main__':
    success = test_super_admin()
    sys.exit(0 if success else 1)
