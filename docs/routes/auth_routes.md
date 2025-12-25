# Auth Routes Documentation

Base URL: `/` (No prefix defined in Blueprint, but routes are at root level)

## Authentication Mechanism

This API uses **JWT (JSON Web Token)** for authentication.
1.  **Login:** Send credentials to `/login`. Receive an `access_token`.
2.  **Store:** Save this token on the client side (e.g., `localStorage`, `sessionStorage`, or memory).
3.  **Use:** Send the token in the `Authorization` header for all protected routes:
    `Authorization: Bearer <your_access_token>`

## 1. Register
- **URL:** `/register`
- **Method:** `POST`
- **Auth Required:** No
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
  - `400 Bad Request`: Missing fields, username/email taken.

## 2. Login
- **URL:** `/login`
- **Method:** `POST`
- **Auth Required:** No
- **Description:** Authenticates a user and returns a JWT access token.
- **Body:**
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response:**
  - `200 OK`: Login successful. Returns the token.
    ```json
    {
      "message": "Login successful",
      "user": {
        "id": 1,
        "username": "example",
        "email": "example@test.com",
        "is_admin": false
      },
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni..."
    }
    ```
  - `400 Bad Request`: Missing email/password.
  - `401 Unauthorized`: Invalid credentials.

## 3. Change Password
- **URL:** `/change-password`
- **Method:** `POST`
- **Auth Required:** Yes
- **Description:** Allows the logged-in user to change their password.
- **Body:**
  ```json
  {
    "current_password": "string",
    "new_password": "string"
  }
  ```
- **Response:**
  - `200 OK`: Password changed successfully.
  - `400 Bad Request`: Missing fields or invalid current password.
  - `401 Unauthorized`: Missing or invalid JWT token.

## 4. Logout
- **URL:** `/logout`
- **Method:** `POST`
- **Auth Required:** No
- **Description:**  For JWT, "logging out" is primarily a client-side action (discarding the token). This endpoint returns a success message for consistency but does not invalidate the token server-side (unless a blocklist is implemented).
- **Response:**
  - `200 OK`: Logged out successfully.
