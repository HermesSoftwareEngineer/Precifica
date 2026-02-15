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

## 1.1 Chat (Async)
- **URL:** `/chat/async`
- **Method:** `POST`
- **Auth Required:** Optional (User ID linked if logged in)
- **Description:** Queues a message and returns immediately. Use SSE to receive the AI response.
- **Body:**
  ```json
  {
    "message": "string" (required),
    "conversation_id": integer (optional)
  }
  ```
- **Response:**
  - `202 Accepted`:
    ```json
    {
      "status": "queued",
      "conversation_id": integer,
      "message_id": integer
    }
    ```

## 2. Evaluation Chat
- **URL:** `/evaluation/<evaluation_id>/chat`
- **Method:** `POST`
- **Auth Required:** Optional (User ID linked if logged in)
- **Description:** Sends a message to the AI bot specifically to discuss or adjust an existing evaluation. If a chat session already exists for this evaluation, it continues it. Otherwise, it starts a new one with a specialized system prompt. To force a new conversation, send `"new_chat": true`. **Note:** Conversations created here are linked to the evaluation and will not appear in the standard conversation list.
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

## 2.1 Evaluation Chat (Async)
- **URL:** `/evaluation/<evaluation_id>/chat/async`
- **Method:** `POST`
- **Auth Required:** Optional (User ID linked if logged in)
- **Description:** Queues a message for an evaluation chat and returns immediately. Use SSE to receive the AI response.
- **Body:**
  ```json
  {
    "message": "string" (required),
    "new_chat": boolean (optional, default: false)
  }
  ```
- **Response:**
  - `202 Accepted`:
    ```json
    {
      "status": "queued",
      "conversation_id": integer,
      "message_id": integer
    }
    ```

## 3. Conversation SSE Stream
- **URL:** `/conversations/<conversation_id>/stream`
- **Method:** `GET`
- **Auth Required:** Optional (same as chat)
- **Description:** Streams AI progress and messages for a conversation.
- **Events:**
  - `connected`
  - `user_message`
  - `ai_message`
  - `error`
- **Frontend example:**
  ```javascript
  const source = new EventSource(`${API_BASE}/bot/conversations/${conversationId}/stream`, {
    withCredentials: true
  });

  source.addEventListener('user_message', (event) => {
    const data = JSON.parse(event.data);
    addMessage(data.message);
  });

  source.addEventListener('ai_message', (event) => {
    const data = JSON.parse(event.data);
    addMessage(data.message);
  });

  source.addEventListener('error', (event) => {
    console.warn('SSE error', event);
  });
  ```
- **Note:** Native `EventSource` cannot set `Authorization` headers. Use cookie-based auth, a polyfill that supports headers, or a custom fetch stream if you must send a bearer token.
