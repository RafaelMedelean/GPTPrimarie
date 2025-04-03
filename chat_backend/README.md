# Chat Application Backend

This is a FastAPI backend for a chat application with a feedback system and role-based access control.

## Features

- **Modular Structure**: Code is organized into separate modules for better maintainability
- **Role-Based Access Control**: Two user roles (normal user & admin) with different permissions
- **User Authentication**: JWT-based authentication with token generation
- **Conversation Management**: Create, read, update, and delete conversations
- **Chat Functionality**: Send messages and receive AI responses
- **Feedback System**: Rate and comment on AI responses
- **Admin Dashboard**: View statistics and manage users (admin only)
- **MongoDB Integration**: Data persistence using MongoDB

## Project Structure

```
chat_backend/
├── app/
│   ├── core/
│   │   └── auth.py           # Authentication and authorization logic
│   ├── db/
│   │   └── database.py       # Database connection and operations
│   ├── models/
│   │   └── models.py         # Pydantic models for data validation
│   ├── routes/
│   │   ├── admin.py          # Admin-only endpoints
│   │   ├── auth.py           # Authentication endpoints
│   │   └── chat.py           # Chat and conversation endpoints
│   └── main.py               # FastAPI app configuration
├── main.py                   # Application entry point
└── requirements.txt          # Project dependencies
```

## User Roles

1. **Normal User**:
   - Can register and login
   - Can create and manage their own conversations
   - Can send messages and receive AI responses
   - Can provide feedback on AI responses

2. **Admin**:
   - Has all normal user permissions
   - Can view all users in the system
   - Can view all conversations from all users
   - Can access statistics and analytics
   - Can view feedback statistics

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up MongoDB:
   - Make sure you have MongoDB running or use MongoDB Atlas
   - Update the MongoDB connection string in `app/db/database.py` if needed

3. Run the server:

```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access the auto-generated API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /token` - Get access token (login)
- `POST /users` - Create a new user (signup)
- `GET /users/me` - Get current user information

### Conversations

- `POST /conversations` - Create a new conversation
- `GET /conversations` - Get all conversations for the current user
- `GET /conversations/{conversation_id}` - Get a specific conversation
- `PUT /conversations/{conversation_id}` - Update a conversation
- `DELETE /conversations/{conversation_id}` - Delete a conversation

### Chat

- `POST /chat` - Send a message and get a response

### Feedback

- `POST /feedback` - Submit feedback for a message

### Admin

- `GET /admin/users` - Get all users
- `GET /admin/conversations` - Get all conversations
- `GET /admin/stats/users` - Get user statistics
- `GET /admin/stats/feedback` - Get feedback statistics
- `GET /admin/dashboard` - Get dashboard data

## Security Notes

- The JWT secret key is hardcoded for demonstration purposes. In a production environment, use a secure key stored in environment variables.
- Password hashing is simplified for demonstration. In a production environment, use a proper password hashing library like passlib with bcrypt.