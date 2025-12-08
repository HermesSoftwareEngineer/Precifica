# Conversation Routes Documentation

Base URL: `/api/conversations`

## 1. List Conversations
- **URL:** `/`
- **Method:** `GET`
- **Auth Required:** Yes
- **Description:** Retrieves a list of all conversations belonging to the authenticated user, ordered by most recently updated.
- **Response:**
  - `200 OK`: List of conversation objects.
    ```json
    [
      {
        "id": 1,
        "user_id": 1,
        "title": "New Conversation",
        "created_at": "2023-10-27T10:00:00",
        "updated_at": "2023-10-27T10:05:00"
      },
      ...
    ]
    ```

## 2. Create Conversation
- **URL:** `/`
- **Method:** `POST`
- **Auth Required:** Yes
- **Description:** Creates a new empty conversation.
- **Body:**
  ```json
  {
    "title": "string" (optional, default "New Conversation")
  }
  ```
- **Response:**
  - `201 Created`: The created conversation object.

## 3. Get Conversation Details
- **URL:** `/<conversation_id>`
- **Method:** `GET`
- **Auth Required:** Yes
- **Description:** Retrieves details of a specific conversation, including its message history.
- **Response:**
  - `200 OK`: Conversation object with messages.
    ```json
    {
      "id": 1,
      "user_id": 1,
      "title": "Real Estate Analysis",
      "created_at": "...",
      "updated_at": "...",
      "messages": [
        {
          "id": 1,
          "conversation_id": 1,
          "sender": "user",
          "content": "Hello",
          "created_at": "..."
        },
        {
          "id": 2,
          "conversation_id": 1,
          "sender": "bot",
          "content": "Hi there! How can I help?",
          "created_at": "..."
        }
      ]
    }
    ```
  - `403 Forbidden`: User does not own the conversation.
  - `404 Not Found`: Conversation ID does not exist.

## 4. Update Conversation Title
- **URL:** `/<conversation_id>`
- **Method:** `PUT`
- **Auth Required:** Yes
- **Description:** Updates the title of a conversation.
- **Body:**
  ```json
  {
    "title": "string" (required)
  }
  ```
- **Response:**
  - `200 OK`: Updated conversation object.
  - `400 Bad Request`: Title missing.

## 5. Delete Conversation
- **URL:** `/<conversation_id>`
- **Method:** `DELETE`
- **Auth Required:** Yes
- **Description:** Permanently deletes a conversation and all its messages.
- **Response:**
  - `200 OK`: Success message.
  - `500 Internal Server Error`: Deletion failed.
