# Bot Routes Documentation

Base URL: `/bot`

## 1. Chat
- **URL:** `/chat`
- **Method:** `POST`
- **Auth Required:** Optional (User ID linked if logged in)
- **Description:** Sends a message to the AI bot. If `conversation_id` is provided, continues that chat. If not, creates a new conversation. All messages are persisted in the database.
- **Body:**
  ```json
  {
    "message": "string" (required),
    "conversation_id": integer (optional)
  }
  ```
- **Response:**
  - `200 OK`:
    ```json
    {
      "response": "string",
      "conversation_id": integer,
      "message_id": integer
    }
    ```
  - `400 Bad Request`: Message is required.
  - `404 Not Found`: Provided `conversation_id` does not exist.
  - `500 Internal Server Error`: Error processing request.

## 2. Evaluation Chat
- **URL:** `/evaluation/<evaluation_id>/chat`
- **Method:** `POST`
- **Auth Required:** Optional (User ID linked if logged in)
- **Description:** Sends a message to the AI bot specifically to discuss or adjust an existing evaluation. If a chat session already exists for this evaluation, it continues it. Otherwise, it starts a new one with a specialized system prompt. To force a new conversation, send `"new_chat": true`.
- **Body:**
  ```json
  {
    "message": "string" (required),
    "new_chat": boolean (optional, default: false)
  }
  ```
- **Response:**
  - `200 OK`:
    ```json
    {
      "response": "string",
      "conversation_id": integer,
      "message_id": integer
    }
    ```
  - `400 Bad Request`: Message is required.
  - `404 Not Found`: Evaluation not found.
  - `500 Internal Server Error`: Error processing request.
