# Auth Routes Documentation

Base URL: `/` (No prefix defined in Blueprint, but routes are at root level)

## 1. Register
- **URL:** `/register`
- **Method:** `POST`
- **Auth Required:** No (Must be logged out)
- **Description:** Registers a new user.
- **Body:**
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Response:**
  - `201 Created`: User created successfully.
  - `400 Bad Request`: Missing fields, username/email taken, or already logged in.

## 2. Login
- **URL:** `/login`
- **Method:** `POST`
- **Auth Required:** No (Must be logged out)
- **Description:** Authenticates a user.
- **Body:**
  ```json
  {
    "email": "string",
    "password": "string",
    "remember": boolean (optional)
  }
  ```
- **Response:**
  - `200 OK`: Login successful.
  - `400 Bad Request`: Missing email/password.
  - `401 Unauthorized`: Invalid credentials.

## 3. Logout
- **URL:** `/logout`
- **Method:** `POST`
- **Auth Required:** Yes (Implicitly, to logout)
- **Description:** Logs out the current user.
- **Response:**
  - `200 OK`: Logged out successfully.
