import os
import motor.motor_asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import uuid
import ssl

from ..models.models import User, UserInDB, Conversation, Message

MONGO_URI = os.getenv("MONGO_URI") or "mongodb://localhost:27017"
DB_NAME = os.getenv("MONGO_DB_NAME") or "chat_app"

# Configure MongoDB client with updated TLS settings
client = motor.motor_asyncio.AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    tlsAllowInvalidCertificates=True  # This replaces ssl_cert_reqs=ssl.CERT_NONE
)

db = client[DB_NAME]

# Collections
users_collection = db["users"]
conversations_collection = db["conversations"]

# Async function to test MongoDB connection; call this in your FastAPI startup event
async def connect_to_mongo():
    try:
        await client.admin.command('ping')
        print("MongoDB connection successful!")
    except Exception as e:
        print(f"MongoDB connection error: {e}")
        # Optionally, handle fallback to a local instance if needed

# User database operations
import asyncio

async def get_user_by_username(username: str) -> Optional[UserInDB]:
    user_doc = await users_collection.find_one({"username": username})

    if user_doc:
        return UserInDB(**user_doc)
    return None

async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    user_doc = await users_collection.find_one({"id": user_id})
    if user_doc:
        return UserInDB(**user_doc)
    return None

async def create_user(username: str, email: str, hashed_password: str, role: str = "user") -> User:
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "role": role,
        "created_at": datetime.utcnow().isoformat()
    }
    await users_collection.insert_one(user_doc)
    
    return User(
        id=user_id,
        username=username,
        email=email,
        role=role,
        created_at=datetime.utcnow()
    )

async def get_all_users() -> List[User]:
    cursor = users_collection.find({})
    users = []
    async for doc in cursor:
        users.append(User(
            id=doc["id"],
            username=doc["username"],
            email=doc["email"],
            role=doc["role"],
            created_at=datetime.fromisoformat(doc["created_at"])
        ))
    return users

# async def create_initial_admin():
#     # Count documents asynchronously with Motor
#     user_count = await users_collection.count_documents({})

#     if user_count == 0:
#         from ..core.auth import get_password_hash
#         hashed_password = get_password_hash("admin123")

#         await create_user(
#             username="admin",
#             email="admin@example.com",
#             hashed_password=hashed_password,
#             role="admin"
#         )
#         print("Created initial admin user: username='admin', password='admin123'")


# Conversation database operations
async def create_conversation(user_id: str, title: str, messages: List[Dict] = None) -> Conversation:
    if messages is None:
        messages = []
    
    conversation_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    conversation_doc = {
        "id": conversation_id,
        "title": title,
        "messages": messages,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "user_id": user_id
    }
    
    await conversations_collection.insert_one(conversation_doc)
    
    return Conversation(
        id=conversation_id,
        title=title,
        messages=[Message(**m) for m in messages],
        created_at=now,
        updated_at=now,
        user_id=user_id
    )

async def get_conversation(conversation_id: str, user_id: Optional[str] = None) -> Optional[Conversation]:
    query = {"id": conversation_id}
    if user_id:
        query["user_id"] = user_id
    
    doc = await conversations_collection.find_one(query)
    if not doc:
        return None
    
    return Conversation(
        id=doc["id"],
        title=doc["title"],
        messages=[Message(**m) for m in doc["messages"]],
        created_at=datetime.fromisoformat(doc["created_at"]),
        updated_at=datetime.fromisoformat(doc["updated_at"]),
        user_id=doc["user_id"]
    )

async def get_user_conversations(user_id: str) -> List[Conversation]:
    cursor = conversations_collection.find({"user_id": user_id})
    conversations = []
    
    async for doc in cursor:
        conversations.append(Conversation(
            id=doc["id"],
            title=doc["title"],
            messages=[Message(**m) for m in doc["messages"]],
            created_at=datetime.fromisoformat(doc["created_at"]),
            updated_at=datetime.fromisoformat(doc["updated_at"]),
            user_id=doc["user_id"]
        ))
    
    return conversations

async def get_all_conversations() -> List[Conversation]:
    cursor = conversations_collection.find({})
    conversations = []
    
    async for doc in cursor:
        conversations.append(Conversation(
            id=doc["id"],
            title=doc["title"],
            messages=[Message(**m) for m in doc["messages"]],
            created_at=datetime.fromisoformat(doc["created_at"]),
            updated_at=datetime.fromisoformat(doc["updated_at"]),
            user_id=doc["user_id"]
        ))
    
    return conversations

async def update_conversation(conversation_id: str, update_data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[Conversation]:
    query = {"id": conversation_id}
    if user_id:
        query["user_id"] = user_id
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    await conversations_collection.update_one(
        query,
        {"$set": update_data}
    )
    
    return await get_conversation(conversation_id, user_id)

async def delete_conversation(conversation_id: str, user_id: Optional[str] = None) -> bool:
    query = {"id": conversation_id}
    if user_id:
        query["user_id"] = user_id
    
    result = await conversations_collection.delete_one(query)
    return result.deleted_count > 0

async def add_messages_to_conversation(conversation_id: str, messages: List[Dict], user_id: Optional[str] = None) -> Optional[Conversation]:
    query = {"id": conversation_id}
    if user_id:
        query["user_id"] = user_id
    
    await conversations_collection.update_one(
        query,
        {
            "$push": {
                "messages": {"$each": messages}
            },
            "$set": {"updated_at": datetime.utcnow().isoformat()}
        }
    )
    
    return await get_conversation(conversation_id, user_id)

async def update_message_feedback(conversation_id: str, message_id: str, feedback: Dict, user_id: Optional[str] = None) -> bool:
    query = {"id": conversation_id}
    if user_id:
        query["user_id"] = user_id
    
    conversation = await get_conversation(conversation_id, user_id)
    if not conversation:
        return False
    
    messages = [m.dict() for m in conversation.messages]
    message_found = False
    
    for msg in messages:
        if msg["id"] == message_id:
            msg["feedback"] = feedback
            message_found = True
            break
    
    if not message_found:
        return False
    
    await conversations_collection.update_one(
        query,
        {
            "$set": {
                "messages": messages,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    return True

# Admin statistics operations
async def get_user_statistics() -> List[Dict]:
    pipeline = [
        {
            "$lookup": {
                "from": "conversations",
                "localField": "id",
                "foreignField": "user_id",
                "as": "conversations"
            }
        },
        {
            "$project": {
                "_id": 0,
                "id": 1,
                "username": 1,
                "email": 1,
                "role": 1,
                "conversation_count": {"$size": "$conversations"},
                "message_count": {
                    "$reduce": {
                        "input": "$conversations.messages",
                        "initialValue": 0,
                        "in": {"$add": ["$$value", {"$size": "$$this"}]}
                    }
                }
            }
        }
    ]
    
    cursor = users_collection.aggregate(pipeline)
    stats = []
    
    async for doc in cursor:
        stats.append(doc)
    
    return stats

async def get_feedback_statistics() -> Dict:
    pipeline = [
        {"$unwind": "$messages"},
        {"$match": {"messages.feedback": {"$ne": None}}},
        {
            "$group": {
                "_id": None,
                "total_count": {"$sum": 1},
                "quality_yes": {"$sum": {"$cond": [{"$eq": ["$messages.feedback.qualityRating", True]}, 1, 0]}},
                "quality_no": {"$sum": {"$cond": [{"$eq": ["$messages.feedback.qualityRating", False]}, 1, 0]}},
                "structure_yes": {"$sum": {"$cond": [{"$eq": ["$messages.feedback.structureRating", True]}, 1, 0]}},
                "structure_no": {"$sum": {"$cond": [{"$eq": ["$messages.feedback.structureRating", False]}, 1, 0]}}
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_count": 1,
                "quality_yes": 1,
                "quality_no": 1,
                "structure_yes": 1,
                "structure_no": 1
            }
        }
    ]
    
    cursor = conversations_collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    
    if not result:
        return {
            "total_feedback_count": 0,
            "quality_stats": {
                "yes_percentage": 0,
                "no_percentage": 0
            },
            "structure_stats": {
                "yes_percentage": 0,
                "no_percentage": 0
            }
        }
    
    stats = result[0]
    total_quality_votes = stats.get("quality_yes", 0) + stats.get("quality_no", 0)
    total_structure_votes = stats.get("structure_yes", 0) + stats.get("structure_no", 0)
    
    # Calculate percentages
    quality_yes_pct = round((stats.get("quality_yes", 0) / total_quality_votes * 100) if total_quality_votes > 0 else 0)
    quality_no_pct = round((stats.get("quality_no", 0) / total_quality_votes * 100) if total_quality_votes > 0 else 0)
    structure_yes_pct = round((stats.get("structure_yes", 0) / total_structure_votes * 100) if total_structure_votes > 0 else 0)
    structure_no_pct = round((stats.get("structure_no", 0) / total_structure_votes * 100) if total_structure_votes > 0 else 0)
    
    return {
        "total_feedback_count": stats.get("total_count", 0),
        "quality_stats": {
            "yes_percentage": quality_yes_pct,
            "no_percentage": quality_no_pct
        },
        "structure_stats": {
            "yes_percentage": structure_yes_pct,
            "no_percentage": structure_no_pct
        }
    }