# Super Admin System

## Overview
The Super Admin system ensures that specific users (global administrators) have automatic and permanent access to all units in the system.

## Features

### Automatic Access
- **Auto-Addition**: Super admins are automatically added to all new units when they are created
- **Role**: Super admins are added with the 'admin' role in each unit
- **Cannot Be Removed**: Super admins cannot be removed from any unit

### Implementation Details

#### 1. Database Level
Super admins are identified by:
```sql
users.is_admin = true
```

#### 2. Model Level (Unit Model)
- **Event Listener**: Automatically adds all `is_admin=true` users when a new unit is created
- **Protection**: `remove_user()` method throws error if trying to remove a super admin

#### 3. Controller Level
- API endpoints prevent removal of super admins
- Returns 403 error if attempted

## Current Super Admins

Currently configured super admin:
- **Email**: hermesbarbosa9@gmail.com
- **Username**: Hermes

## Scripts

### Promote User to Super Admin
```bash
python scripts/promote_super_admin.py
```

This script:
1. Sets `is_admin = True`
2. Adds user to all existing units as 'admin'
3. Sets active_unit_id if not set

### Test Super Admin Functionality
```bash
python scripts/test_super_admin.py
```

This script verifies:
1. Super admin has access to all units
2. New units automatically add super admin
3. Super admin cannot be removed

## API Behavior

### Creating Units
When a new unit is created via `POST /api/units`, all super admins are automatically added as members with 'admin' role.

### Removing Users
Attempting to remove a super admin via `DELETE /api/units/<id>/users` will return:
```json
{
  "error": "Cannot remove global admin from units"
}
```
Status Code: 403 Forbidden

## Code Examples

### Check if User is Super Admin
```python
from app.models import User

user = User.query.get(user_id)
if user.is_admin:
    print("This user is a super admin")
```

### Add Another Super Admin
```python
from app import db
from app.models import User, Unit

# 1. Set user as global admin
user = User.query.filter_by(email='new.admin@example.com').first()
user.is_admin = True

# 2. Add to all existing units
all_units = Unit.query.all()
for unit in all_units:
    if not user.units.filter_by(id=unit.id).first():
        unit.add_user(user, role='admin')

db.session.commit()
```

## Security Considerations

1. **Permanent Access**: Super admins cannot be locked out of units
2. **Unit Isolation**: While super admins have access to all units, they still need to select an active unit to interact with data
3. **Audit Trail**: All actions should be logged with user identification

## Troubleshooting

### Super Admin Not Added to Existing Units
Run the promotion script:
```bash
python scripts/promote_super_admin.py
```

### Super Admin Not Auto-Added to New Unit
1. Check `user.is_admin` is `True`
2. Verify event listener is registered (should happen automatically)
3. Check database logs for any constraint violations

### Need to Add Another Super Admin
Edit `scripts/promote_super_admin.py` and change the email:
```python
SUPER_ADMIN_EMAIL = 'new.admin@example.com'
```
Then run the script.

## Future Enhancements

Possible improvements:
1. **Super Admin List**: Store super admin emails in config/environment variable
2. **Audit Logging**: Log all super admin actions
3. **Temporary Super Admin**: Time-limited super admin access
4. **Super Admin Dashboard**: Special UI for super admins to manage all units
