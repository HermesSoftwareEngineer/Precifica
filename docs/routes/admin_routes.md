# Admin Routes Documentation

Base URL: `/admin`

## 1. List Users
- **URL:** `/users`
- **Method:** `GET`
- **Auth Required:** Yes (Login + Admin)
- **Description:** Retrieves a list of all users.
- **Response:**
  - `200 OK`: List of user objects.

## 2. Create User
- **URL:** `/users`
- **Method:** `POST`
- **Auth Required:** Yes (Login + Admin)
- **Description:** Creates a new user.
- **Body:**
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string",
    "is_admin": boolean (optional, default false)
  }
  ```
- **Response:**
  - `201 Created`: User created successfully.
  - `400 Bad Request`: Missing fields or username/email already taken.

## 3. Edit User
- **URL:** `/users/<user_id>`
- **Method:** `PUT`
- **Auth Required:** Yes (Login + Admin)
- **Description:** Updates an existing user.
- **Body:**
  ```json
  {
    "username": "string",
    "email": "string",
    "is_admin": boolean,
    "password": "string" (optional)
  }
  ```
- **Response:**
  - `200 OK`: User updated successfully.
  - `400 Bad Request`: Username/email already taken.

## 4. Delete User
- **URL:** `/users/<user_id>`
- **Method:** `DELETE`
- **Auth Required:** Yes (Login + Admin)
- **Description:** Deletes a user.
- **Response:**
  - `200 OK`: User deleted successfully.
