# Units Feature Implementation Guide

## Overview
This document describes the implementation of the Units feature in the Precifica system. Units represent imobiliaries or specific brokers with their own users and isolated data.

## Architecture

### Key Concepts
- **Unit**: A group/organization that can have multiple users and isolated data
- **Users in Unit**: Users can belong to multiple units with different roles
- **Active Unit**: Each user has an "active unit" which scopes all their data access
- **User Roles**: Admin, Manager, Member

### Data Isolation
All data is isolated by unit:
- Evaluations belong to one unit
- Conversations belong to one unit
- Users see only data from their active unit

## Database Changes

### New Tables

#### `units` Table
```sql
CREATE TABLE units (
    id INTEGER PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(120),
    phone VARCHAR(20),
    logo_url VARCHAR(255),
    custom_fields JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

#### `user_units` Table (M2M Association)
```sql
CREATE TABLE user_units (
    user_id INTEGER PRIMARY KEY FOREIGN KEY(users.id),
    unit_id INTEGER PRIMARY KEY FOREIGN KEY(units.id),
    role VARCHAR(50) DEFAULT 'member',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Modified Tables

#### `users` Table
- Added column: `active_unit_id` (INTEGER, FK to units.id)
- This tracks which unit the user is currently using

#### `evaluations` Table
- Added column: `unit_id` (INTEGER, FK to units.id) - NOT NULL
- Ensures each evaluation belongs to exactly one unit

#### `conversations` Table
- Added column: `unit_id` (INTEGER, FK to units.id) - NOT NULL
- Ensures each conversation belongs to exactly one unit

## Code Changes

### New Files Created

#### Models
- `app/models/unit.py` - Unit model with M2M relationship to User

#### Controllers
- `app/controllers/unit_controller.py` - Business logic for unit operations

#### Routes
- `app/routes/unit_routes.py` - API endpoints for unit management

#### Utilities
- `app/utils/unit_helpers.py` - Helper functions for unit operations
- Enhanced `app/utils/decorators.py` - Added unit-related decorators

#### Scripts
- `scripts/add_units_support.py` - Migration script to initialize units

#### Documentation
- `docs/routes/unit_routes.md` - Complete API documentation

### Modified Files
- `app/models/user.py` - Added active_unit_id and relationship
- `app/models/evaluation.py` - Added unit_id and updated to_dict()
- `app/models/chat.py` - Added unit_id and updated to_dict()
- `app/models/__init__.py` - Updated imports
- `app/__init__.py` - Registered unit_bp blueprint

## Installation & Setup

### 1. Update Database
Run the migration script to add the new tables and columns:

```bash
python scripts/add_units_support.py
```

This script will:
1. Create the `units` table
2. Create the `user_units` association table
3. Add `unit_id` columns to `evaluations` and `conversations`
4. Add `active_unit_id` column to `users`
5. Create a default unit
6. Associate all existing users with the default unit
7. Associate all existing evaluations/conversations with the default unit

### 2. Update Code
Ensure all imports are working:

```bash
python -c "from app import create_app; app = create_app()"
```

## API Usage

### User Workflow

1. **Login** (existing endpoint):
   ```bash
   POST /api/auth/login
   ```
   Gets JWT token

2. **List User's Units**:
   ```bash
   GET /api/units
   ```
   Returns all units the user belongs to

3. **Set Active Unit**:
   ```bash
   POST /api/units/<unit_id>/set-active
   ```
   Sets the active unit for the current user

4. **Create New Unit** (if user is admin):
   ```bash
   POST /api/units
   {
     "name": "New Imobiliaria",
     "email": "contact@newimob.com",
     "phone": "+55 11 1234-5678"
   }
   ```

5. **Add Users to Unit** (unit admin only):
   ```bash
   POST /api/units/<unit_id>/users
   {
     "user_id": 2,
     "role": "member"
   }
   ```

## Decorators & Helpers

### New Decorators

```python
from app.utils.decorators import unit_required, unit_admin_required

@unit_required  # Ensures user has active unit set
@unit_admin_required  # Ensures user is admin/manager of active unit
```

### Helper Functions

```python
from app.utils.unit_helpers import (
    get_user_active_unit,
    get_user_units,
    check_unit_access,
    check_unit_admin_access
)

# Get current user's active unit
active = get_user_active_unit()

# Check if user can access a specific unit
has_access = check_unit_access(unit_id)

# Check if user is admin of a unit
is_admin = check_unit_admin_access(unit_id)
```

## Integrating with Existing Controllers

To add unit filtering to existing controllers, follow this pattern:

```python
from flask_jwt_extended import get_jwt_identity
from app.models import User

@app.route('/api/evaluations')
@jwt_required()
def list_evaluations():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    # Filter by active unit
    evaluations = user.active_unit.evaluations.all()
    return jsonify([e.to_dict() for e in evaluations])
```

## Backward Compatibility

The migration script ensures backward compatibility:
- All existing users are automatically added to a "Default Unit"
- All existing evaluations/conversations are associated with the default unit
- Users can continue working as before, but now within the default unit context

## Future Enhancements

1. **Role-based permissions** - Implement more granular permission system
2. **Unit-specific settings** - Store configuration per unit
3. **Usage analytics** - Track unit-level analytics
4. **Audit logs** - Log all unit-related actions
5. **Bulk user import** - Import multiple users to a unit
6. **Unit templates** - Create units from templates

## Troubleshooting

### Error: "No active unit selected"
Solution: User needs to call `POST /api/units/<unit_id>/set-active` first

### Error: "Admin/Manager access required"
Solution: Only unit admins/managers can perform this action. Check user's role in the unit.

### Error: "Access denied"
Solution: User doesn't belong to this unit. Ask an admin to add them.

## Testing

Run the migration script to populate test data:

```bash
# Create app context and test
python
>>> from app import create_app, db
>>> from app.models import Unit, User
>>> app = create_app()
>>> with app.app_context():
>>>     units = Unit.query.all()
>>>     print(f"Total units: {len(units)}")
>>>     for unit in units:
>>>         print(f"Unit: {unit.name}, Users: {unit.users.count()}")
```

## Support

For issues or questions about the Units system, refer to:
- [Unit Routes Documentation](./routes/unit_routes.md)
- Source code comments in `app/models/unit.py`
- Example usage in `app/controllers/unit_controller.py`
