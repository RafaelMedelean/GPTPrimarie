from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict

from ..models.models import User, Conversation, UserStats, FeedbackStats
from ..core.auth import get_admin_user
from ..db.database import (
    get_all_users,
    get_all_conversations,
    get_user_statistics,
    get_feedback_statistics
)

router = APIRouter(prefix="/admin", tags=["admin"])

# Admin routes for user management
@router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_admin_user)):
    """
    Get all users in the system.
    Only accessible to admin users.
    """
    return await get_all_users()

# Admin routes for conversation management
@router.get("/conversations", response_model=List[Conversation])
async def get_all_user_conversations(current_user: User = Depends(get_admin_user)):
    """
    Get all conversations from all users.
    Only accessible to admin users.
    """
    return await get_all_conversations()

# Admin routes for statistics
@router.get("/stats/users", response_model=List[Dict])
async def get_user_stats(current_user: User = Depends(get_admin_user)):
    """
    Get statistics about all users.
    Only accessible to admin users.
    """
    return await get_user_statistics()

@router.get("/stats/feedback", response_model=Dict)
async def get_feedback_stats(current_user: User = Depends(get_admin_user)):
    """
    Get statistics about feedback.
    Only accessible to admin users.
    """
    return await get_feedback_statistics()

# Admin dashboard data
@router.get("/dashboard")
async def get_dashboard_data(current_user: User = Depends(get_admin_user)):
    """
    Get combined dashboard data for admin.
    Only accessible to admin users.
    """
    users = await get_all_users()
    user_stats = await get_user_statistics()
    feedback_stats = await get_feedback_statistics()
    
    # Count total conversations and messages
    total_conversations = sum(stat.get("conversation_count", 0) for stat in user_stats)
    total_messages = sum(stat.get("message_count", 0) for stat in user_stats)
    
    return {
        "total_users": len(users),
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "feedback_stats": feedback_stats,
        "user_stats": user_stats
    }

@router.get("/questions", response_model=List[Dict])
async def get_questions_with_feedback(current_user: User = Depends(get_admin_user)):
    """Get all question-response pairs with their quality and structure feedback."""
    # Retrieve all conversations
    conversations = await get_all_conversations()
    questions = []
    
    # Iterate over each conversation
    for conv in conversations:
        # Iterate over messages in the conversation
        for i, msg in enumerate(conv.messages):
            if msg.role == "user":
                # Find the first assistant response following the user message
                response_msg = None
                for j in range(i + 1, len(conv.messages)):
                    if conv.messages[j].role == "assistant":
                        response_msg = conv.messages[j]
                        break
                
                # Add all assistant messages, even without feedback
                if response_msg is not None:
                    feedback_data = {
                        "quality_rating": None,
                        "structure_rating": None,
                        "quality_comment": "",
                        "structure_comment": ""
                    }
                    
                    if response_msg.feedback is not None:
                        # Convert boolean to 1/0 for frontend display
                        quality_rating = int(response_msg.feedback.qualityRating) if response_msg.feedback.qualityRating is not None else None
                        structure_rating = int(response_msg.feedback.structureRating) if response_msg.feedback.structureRating is not None else None
                        
                        feedback_data = {
                            "quality_rating": quality_rating,
                            "structure_rating": structure_rating,
                            "quality_comment": response_msg.feedback.qualityComment or "",
                            "structure_comment": response_msg.feedback.structureComment or ""
                        }
                    
                    questions.append({
                        "id": response_msg.id,  # Include message ID for reference
                        "conversation_id": conv.id,
                        "question": msg.content,
                        "response": response_msg.content,
                        "asked_at": conv.created_at,
                        "has_feedback": response_msg.feedback is not None,
                        **feedback_data
                    })
    
    # Sort by creation date, newest first
    questions.sort(key=lambda x: x["asked_at"], reverse=True)
    return questions