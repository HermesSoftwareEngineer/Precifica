# Unit Routes Documentation

## Overview
The Unit Routes provide endpoints for managing units within the system. Units represent imobiliaries or specific brokers with isolated data and user hierarchies.

## Authentication
All endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <access_token>
```

## Base URL
```
/api/units
```

---

## Endpoints

### Create Unit
**POST** `/api/units`

Creates a new unit and adds the current user as an admin.

**Request Body:**
```json
{
  "name": "string (required)",
  "email": "string (optional)",
  "phone": "string (optional)",
  "whatsapp": "string (optional)",
  "address": "string (optional)",
  "cnpj": "string (optional)",
  "logo_url": "string (optional)",
  "custom_fields": "object (optional)"
}
```

**Response (201 Created):**
```json
{
  "message": "Unit created successfully",
  "unit": {
    "id": 1,
    "name": "Imobiliaria XYZ",
    "email": "contact@xyz.com",
    "phone": "+55 11 1234-5678",
    "whatsapp": "+55 11 98765-4321",
    "address": "Rua das Flores, 123 - São Paulo, SP",
    "cnpj": "12.345.678/0001-90",
    "logo_url": "https://...",
    "custom_fields": {},
    "users": [
      {
        "id": 1,
        "username": "user1",
        "email": "user1@example.com",
        "role": "admin"
      }
    ],
    "created_at": "2026-02-17T10:30:00",
    "updated_at": "2026-02-17T10:30:00"
  }
}
```

---

### Get Unit
**GET** `/api/units/<unit_id>`

Get details of a specific unit. User must have access to the unit.

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Imobiliaria XYZ",
  "email": "contact@xyz.com",
  "phone": "+55 11 1234-5678",
  "whatsapp": "+55 11 98765-4321",
  "address": "Rua das Flores, 123 - São Paulo, SP",
  "cnpj": "12.345.678/0001-90",
  "logo_url": "https://...",
  "custom_fields": {},
  "users": [
    {
      "id": 1,
      "username": "user1",
      "email": "user1@example.com",
      "role": "admin"
    },
    {
      "id": 2,
      "username": "user2",
      "email": "user2@example.com",
      "role": "member"
    }
  ],
  "created_at": "2026-02-17T10:30:00",
  "updated_at": "2026-02-17T10:30:00"
}
```

**Error Responses:**
- `404 Not Found`: Unit does not exist
- `403 Forbidden`: User does not have access to this unit

---

### List User's Units
**GET** `/api/units`

List all units the current user belongs to.

**Response (200 OK):**
```json
{
  "units": [
    {
      "id": 1,
      "name": "Imobiliaria XYZ",
      "email": "contact@xyz.com",
      "phone": "+55 11 1234-5678",
      "whatsapp": "+55 11 98765-4321",
      "address": "Rua das Flores, 123 - São Paulo, SP",
      "cnpj": "12.345.678/0001-90",
      "logo_url": "https://...",
      "custom_fields": {},
      "created_at": "2026-02-17T10:30:00",
      "updated_at": "2026-02-17T10:30:00"
    },
    {
      "id": 2,
      "name": "Corretoria ABC",
      "email": "contact@abc.com",
      "phone": "+55 21 9876-5432",
      "whatsapp": "+55 21 99999-8888",
      "address": "Av. Principal, 456 - Rio de Janeiro, RJ",
      "cnpj": "98.765.432/0001-10",
      "logo_url": "https://...",
      "custom_fields": {},
      "created_at": "2026-02-17T11:45:00",
      "updated_at": "2026-02-17T11:45:00"
    }
  ],
  "active_unit_id": 1
}
```

---

### Update Unit
**PUT** `/api/units/<unit_id>`

Update unit details. Requires admin/manager access to the unit.

**Request Body (all fields optional):**
```json
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "whatsapp": "string",
  "address": "string",
  "cnpj": "string",
  "logo_url": "string",
  "custom_fields": "object"
}
```

**Response (200 OK):**
```json
{
  "message": "Unit updated successfully",
  "unit": {
    "id": 1,
    "name": "Updated Unit Name",
    ...
  }
}
```

**Error Responses:**
- `404 Not Found`: Unit does not exist
- `403 Forbidden`: User is not admin/manager of this unit

---

### Set Active Unit
**POST** `/api/units/<unit_id>/set-active`

Set the active unit for the current user. All future requests will be scoped to this unit.

**Response (200 OK):**
```json
{
  "message": "Active unit updated successfully",
  "active_unit_id": 1
}
```

**Error Responses:**
- `404 Not Found`: Unit does not exist
- `403 Forbidden`: User does not have access to this unit

---

### Add User to Unit
**POST** `/api/units/<unit_id>/users`

Add a user to a unit. Requires admin/manager access to the unit.

**Request Body:**
```json
{
  "user_id": 2,
  "role": "member"  // "admin", "manager", or "member"
}
```

**Response (200 OK):**
```json
{
  "message": "User added to unit successfully",
  "unit": {
    "id": 1,
    "name": "Imobiliaria XYZ",
    "users": [
      {
        "id": 1,
        "username": "user1",
        "email": "user1@example.com",
        "role": "admin"
      },
      {
        "id": 2,
        "username": "user2",
        "email": "user2@example.com",
        "role": "member"
      }
    ],
    ...
  }
}
```

**Error Responses:**
- `400 Bad Request`: user_id is required
- `404 Not Found`: Unit or user does not exist
- `403 Forbidden`: User is not admin/manager of this unit

---

### Remove User from Unit
**DELETE** `/api/units/<unit_id>/users`

Remove a user from a unit. Requires admin/manager access to the unit.

**Request Body:**
```json
{
  "user_id": 2
}
```

**Response (200 OK):**
```json
{
  "message": "User removed from unit successfully",
  "unit": {
    "id": 1,
    "name": "Imobiliaria XYZ",
    "users": [
      {
        "id": 1,
        "username": "user1",
        "email": "user1@example.com",
        "role": "admin"
      }
    ],
    ...
  }
}
```

**Error Responses:**
- `400 Bad Request`: user_id is required or attempting to remove last admin
- `404 Not Found`: Unit or user does not exist
- `403 Forbidden`: User is not admin/manager of this unit

---

## User Roles

### Admin
- Can manage all unit settings
- Can add/remove users
- Can modify user roles
- Full access to unit data

### Manager
- Can manage most unit settings
- Can add/remove members
- Cannot modify other managers or admins
- Full access to unit data

### Member
- Can view unit data according to their permissions
- Cannot manage unit settings
- Cannot add/remove users
- Access follows unit-level data isolation

---

## Data Isolation

All data in the system is isolated by unit:
- **Evaluations**: Each evaluation belongs to a specific unit
- **Conversations**: Each conversation belongs to a specific unit
- **Users**: Can belong to multiple units but see data only from their active unit

When a user sets an active unit, all subsequent API calls are scoped to that unit's data.

---

## Register User in Unit
**POST** `/api/units/register-user`

Register a new user and automatically add them to the current admin/manager's active unit.

**Authorization:**
- Requires `@jwt_required`
- Requires `@unit_admin_required` (user must be admin or manager of their active unit)

**Permissions:**
- **Admins** can create users with any role (admin, manager, member)
- **Managers** can only create users with 'manager' or 'member' roles (cannot create admins)

**Request Body:**
```json
{
  "username": "string (required, max 100 chars)",
  "email": "string (required)",
  "password": "string (required)",
  "role": "string (optional, default: 'member')" // Can be 'admin', 'manager', or 'member'
}
```

**Response (201 Created):**
```json
{
  "message": "User registered successfully and added to unit 'Imobiliaria XYZ'",
  "user": {
    "id": 5,
    "username": "newuser",
    "email": "newuser@example.com",
    "role": "member",
    "unit": {
      "id": 1,
      "name": "Imobiliaria XYZ",
      "email": "contact@xyz.com",
      "phone": "+55 11 1234-5678",
      "created_at": "2026-02-17T10:30:00",
      "updated_at": "2026-02-17T10:30:00"
    },
    "active_unit_id": 1
  }
}
```

**Error Responses:**
- `400 Bad Request`: 
  - Missing required fields (username, email, password)
  - Email already registered
  - Username already taken
  - Invalid role
  - No active unit selected
- `403 Forbidden`: 
  - User is not admin/manager of their active unit
  - Manager trying to create admin user (only admins can create admins)
- `404 Not Found`: Active unit not found

**Notes:**
- The new user is automatically added to the admin/manager's active unit
- The new user's active_unit_id is set to this unit
- Only admins and managers can register new users
- Managers cannot create admin users (only admins can)
- Username can have up to 100 characters

---

## Update User in Unit
**PUT** `/api/units/users/<user_id>`

Update a user's information in the current admin/manager's active unit. Cannot update passwords.

**Authorization:**
- Requires `@jwt_required`
- Requires `@unit_admin_required` (user must be admin or manager of their active unit)

**Permissions:**
- **Admins** can edit any user in the unit (except global admins)
- **Managers** can edit managers and members (cannot edit admins)
- **Managers** cannot promote users to admin role

**Request Body:**
```json
{
  "username": "string (optional, max 100 chars)",
  "email": "string (optional)",
  "role": "string (optional)" // Can be 'admin', 'manager', or 'member'
}
```

**Response (200 OK):**
```json
{
  "message": "User updated successfully",
  "user": {
    "id": 5,
    "username": "updated_username",
    "email": "updated@example.com",
    "role": "manager",
    "unit": {
      "id": 1,
      "name": "Imobiliaria XYZ",
      "email": "contact@xyz.com",
      "phone": "+55 11 1234-5678",
      "created_at": "2026-02-17T10:30:00",
      "updated_at": "2026-02-17T10:30:00"
    }
  }
}
```

**Error Responses:**
- `400 Bad Request`: 
  - Email already registered (by another user)
  - Username already taken (by another user)
  - Invalid role
  - Cannot demote the last admin of the unit
  - No active unit selected
- `403 Forbidden`: 
  - User is not admin/manager of their active unit
  - Manager trying to edit admin user
  - Manager trying to promote user to admin
- `404 Not Found`: 
  - User not found
  - User is not a member of this unit
  - Active unit not found

**Notes:**
- Password cannot be updated through this endpoint (use `/auth/change-password`)
- All fields are optional - only send the fields you want to update
- Changing role requires proper permissions
- Cannot demote the last admin in a unit

---

## Delete User from Unit
**DELETE** `/api/units/users/<user_id>`

Delete a user completely from the system. The user must be a member of the current admin/manager's active unit.

**Authorization:**
- Requires `@jwt_required`
- Requires `@unit_admin_required` (user must be admin or manager of their active unit)

**Permissions:**
- **Admins** can delete any user from the system (except global admins and themselves)
- **Managers** can delete managers and members (cannot delete admins)

**Response (200 OK):**
```json
{
  "message": "User deleted successfully",
  "deleted_user_id": 5
}
```

**Error Responses:**
- `400 Bad Request`: 
  - Cannot delete yourself
  - Cannot delete the last admin of the unit
  - No active unit selected
- `403 Forbidden`: 
  - User is not admin/manager of their active unit
  - Manager trying to delete admin user
  - Cannot delete global admin users
- `404 Not Found`: 
  - User not found
  - User is not a member of this unit
  - Active unit not found

**Notes:**
- ⚠️ **This action is PERMANENT** - The user account is deleted completely from the system
- The user is removed from ALL units before deletion
- Conversations created by this user will have their user_id set to NULL (conversations are preserved)
- Evaluations created in the units remain intact (evaluations are linked to units, not users)
- Cannot delete yourself
- Cannot delete global admin users
- Cannot delete the last admin from a unit

---

## Upload Unit Logo
**POST** `/api/units/<unit_id>/logo`

Upload a logo image for a unit. Only accessible by admins/managers of the unit.

**Authorization:**
- Requires `@jwt_required`
- User must be admin or manager of the unit

**Request:**
- Content-Type: `multipart/form-data`
- Field name: `logo`
- Allowed file types: PNG, JPG, JPEG, GIF, WEBP
- Max file size: 5MB

**Response (200 OK):**
```json
{
  "message": "Logo uploaded successfully",
  "logo_url": "/api/uploads/unit_logos/unit_4_a1b2c3d4.png"
}
```

**Error Responses:**
- `400 Bad Request`: 
  - No file provided
  - Invalid file type
  - File too large
- `403 Forbidden`: User is not admin/manager of this unit
- `404 Not Found`: Unit not found

**Notes:**
- Replaces existing logo automatically
- File is saved with a unique name to prevent conflicts
- Returns a URL that can be used to access the logo

**Example:**
```bash
curl -X POST http://localhost:5000/api/units/1/logo \
  -H "Authorization: Bearer <token>" \
  -F "logo=@/path/to/logo.png"
```

---

## Delete Unit Logo
**DELETE** `/api/units/<unit_id>/logo`

Delete the logo of a unit. Only accessible by admins/managers of the unit.

**Authorization:**
- Requires `@jwt_required`
- User must be admin or manager of the unit

**Response (200 OK):**
```json
{
  "message": "Logo deleted successfully"
}
```

**Error Responses:**
- `403 Forbidden`: User is not admin/manager of this unit
- `404 Not Found`: Unit not found

**Notes:**
- Removes the logo file from the server
- Sets logo_url to NULL in the database

---

## Unit Selection Flow

1. User authenticates and receives JWT token
2. User calls `GET /api/units` to see available units
3. User calls `POST /api/units/<unit_id>/set-active` to select active unit
4. All subsequent requests use the active unit context
5. User can switch units at any time with another set-active call

---

## Examples

### Create a new unit and select it
```bash
# Create unit
curl -X POST http://localhost:5000/api/units \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Imobiliaria",
    "email": "contact@myimob.com",
    "phone": "+55 11 1234-5678",
    "whatsapp": "+55 11 98765-4321",
    "address": "Rua das Flores, 123 - São Paulo, SP",
    "cnpj": "12.345.678/0001-90"
  }'

# Set as active
curl -X POST http://localhost:5000/api/units/1/set-active \
  -H "Authorization: Bearer <token>"
```

### Add a user to your unit
```bash
curl -X POST http://localhost:5000/api/units/1/users \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "role": "member"
  }'
```

### Register a new user in your unit (admin/manager only)
```bash
curl -X POST http://localhost:5000/api/units/register-user \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "novocolaborador",
    "email": "colaborador@empresa.com",
    "password": "senha123",
    "role": "member"
  }'
```

### Update a user in your unit (admin/manager only)
```bash
# Update username and promote to manager
curl -X PUT http://localhost:5000/api/units/users/5 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "novo_nome",
    "role": "manager"
  }'

# Update only email
curl -X PUT http://localhost:5000/api/units/users/5 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@empresa.com"
  }'
```

### Delete a user from your unit (admin/manager only)
```bash
curl -X DELETE http://localhost:5000/api/units/users/5 \
  -H "Authorization: Bearer <token>"
```

### Upload a logo for your unit
```bash
# Upload logo
curl -X POST http://localhost:5000/api/units/1/logo \
  -H "Authorization: Bearer <token>" \
  -F "logo=@/path/to/your/logo.png"

# Delete logo
curl -X DELETE http://localhost:5000/api/units/1/logo \
  -H "Authorization: Bearer <token>"
```

### List all your units
```bash
curl -X GET http://localhost:5000/api/units \
  -H "Authorization: Bearer <token>"
```
