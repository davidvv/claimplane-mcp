"""Chat router for chatbot functionality."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatSession, ChatMessage, User
from app.schemas import ChatMessageRequest, ChatMessageResponse, ChatSessionResponse
from app.services.chat_service import ChatService
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/send", response_model=ChatMessageResponse)
async def send_message(
    message_request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatMessageResponse:
    """Send a chat message and get a response."""
    try:
        chat_service = ChatService(db)
        
        # Get or create chat session
        session = chat_service.get_or_create_session(
            session_id=message_request.sessionId,
            user_id=current_user.id
        )
        
        # Save user message
        chat_service.save_message(
            session_id=session.session_id,
            message=message_request.message,
            sender="user"
        )
        
        # Generate bot response
        response = chat_service.generate_response(
            session_id=session.session_id,
            user_message=message_request.message
        )
        
        # Save bot response
        chat_service.save_message(
            session_id=session.session_id,
            message=response["reply"],
            sender="bot"
        )
        
        return ChatMessageResponse(**response)
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing message"
        )


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatSessionResponse:
    """Create a new chat session."""
    try:
        chat_service = ChatService(db)
        session = chat_service.create_session(user_id=current_user.id)
        
        return ChatSessionResponse(
            sessionId=session.session_id,
            createdAt=session.created_at
        )
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating chat session"
        )


@router.get("/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, str]]:
    """Get chat history for a session."""
    try:
        chat_service = ChatService(db)
        
        # Verify session belongs to user
        session = chat_service.get_session(session_id)
        if not session or (session.user_id and session.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Get message history
        messages = chat_service.get_session_history(session_id)
        
        return [
            {
                "sender": msg.sender,
                "message": msg.message,
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving chat history"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete a chat session."""
    try:
        chat_service = ChatService(db)
        
        # Verify session belongs to user
        session = chat_service.get_session(session_id)
        if not session or (session.user_id and session.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Delete session and messages
        chat_service.delete_session(session_id)
        
        return {"message": "Chat session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting chat session"
        )


@router.get("/intents")
async def get_available_intents() -> Dict[str, str]:
    """Get available chat intents and their descriptions."""
    return {
        "greeting": "General greeting and welcome message",
        "compensation": "Information about compensation amounts and eligibility",
        "eligible": "Eligibility criteria for claims",
        "timeframe": "Time limits for submitting claims",
        "documents": "Required documents for claims",
        "status": "Claim status inquiries",
        "general": "General questions and information"
    }


@router.post("/sessions/{session_id}/clear")
async def clear_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """Clear all messages from a chat session."""
    try:
        chat_service = ChatService(db)
        
        # Verify session belongs to user
        session = chat_service.get_session(session_id)
        if not session or (session.user_id and session.user_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Clear messages
        chat_service.clear_session_messages(session_id)
        
        return {"message": "Chat session cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing chat session"
        )