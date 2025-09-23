"""Chat service for chatbot functionality."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from app.models import ChatSession, ChatMessage, User
from app.config import settings

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat functionality."""
    
    def __init__(self, db: Session):
        """Initialize chat service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID.
        
        Returns:
            str: Unique session ID
        """
        return f"sess_{uuid.uuid4().hex[:16]}"
    
    def create_session(self, user_id: Optional[int] = None) -> ChatSession:
        """Create a new chat session.
        
        Args:
            user_id: Optional user ID to associate with session
            
        Returns:
            ChatSession: Created session
        """
        try:
            session = ChatSession(
                session_id=self.generate_session_id(),
                user_id=user_id
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(f"Created chat session: {session.session_id}")
            return session
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating chat session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[ChatSession]: Session if found
        """
        return self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
    
    def get_or_create_session(
        self,
        session_id: str,
        user_id: Optional[int] = None
    ) -> ChatSession:
        """Get existing session or create new one.
        
        Args:
            session_id: Session ID
            user_id: Optional user ID
            
        Returns:
            ChatSession: Existing or new session
        """
        session = self.get_session(session_id)
        if session:
            return session
        
        # Create new session
        return self.create_session(user_id)
    
    def save_message(
        self,
        session_id: str,
        message: str,
        sender: str
    ) -> ChatMessage:
        """Save a chat message.
        
        Args:
            session_id: Session ID
            message: Message content
            sender: Sender type ('user' or 'bot')
            
        Returns:
            ChatMessage: Saved message
        """
        try:
            chat_message = ChatMessage(
                session_id=session_id,
                message=message,
                sender=sender
            )
            
            self.db.add(chat_message)
            self.db.commit()
            self.db.refresh(chat_message)
            
            logger.debug(f"Saved {sender} message in session {session_id}")
            return chat_message
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving message: {e}")
            raise
    
    def get_session_history(self, session_id: str) -> List[ChatMessage]:
        """Get message history for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List[ChatMessage]: Message history
        """
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
    
    def clear_session_messages(self, session_id: str) -> int:
        """Clear all messages from a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            int: Number of messages deleted
        """
        try:
            deleted_count = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleared {deleted_count} messages from session {session_id}")
            return deleted_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing session messages: {e}")
            raise
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages.
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            # Delete messages first
            self.clear_session_messages(session_id)
            
            # Delete session
            deleted_count = self.db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).delete()
            
            self.db.commit()
            
            if deleted_count > 0:
                logger.info(f"Deleted chat session: {session_id}")
                return True
            else:
                return False
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting session: {e}")
            raise
    
    def generate_response(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, any]:
        """Generate a response to a user message.
        
        Args:
            session_id: Session ID
            user_message: User's message
            
        Returns:
            Dict[str, any]: Response data
        """
        try:
            message_lower = user_message.lower()
            
            # Determine intent and generate response
            if any(word in message_lower for word in ["hello", "hi", "hey", "greeting"]):
                intent = "greeting"
                reply = self.get_greeting_response()
                confidence = 0.9
            elif any(word in message_lower for word in ["compensation", "money", "amount", "euro", "€"]):
                intent = "compensation"
                reply = self.get_compensation_response()
                confidence = 0.9
            elif any(word in message_lower for word in ["eligible", "qualify", "can i", "am i"]):
                intent = "eligible"
                reply = self.get_eligibility_response()
                confidence = 0.8
            elif any(word in message_lower for word in ["time", "long", "when", "deadline", "limit"]):
                intent = "timeframe"
                reply = self.get_timeframe_response()
                confidence = 0.8
            elif any(word in message_lower for word in ["document", "need", "require", "what do i", "boarding pass"]):
                intent = "documents"
                reply = self.get_documents_response()
                confidence = 0.8
            elif any(word in message_lower for word in ["status", "check", "where", "progress"]):
                intent = "status"
                reply = self.get_status_response()
                confidence = 0.7
            else:
                intent = "general"
                reply = self.get_general_response()
                confidence = 0.5
            
            logger.info(f"Generated {intent} response with confidence {confidence}")
            
            return {
                "success": True,
                "reply": reply,
                "intent": intent,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "success": True,
                "reply": "I apologize, but I encountered an error. Please try again.",
                "intent": "error",
                "confidence": 1.0
            }
    
    def get_greeting_response(self) -> str:
        """Get greeting response."""
        return (
            "Hello! I'm here to help you with your flight compensation claim. "
            "How can I assist you today? I can provide information about:\n\n"
            "• Compensation amounts and eligibility\n"
            "• Required documents\n"
            "• Time limits for claims\n"
            "• How to check your claim status\n\n"
            "What would you like to know?"
        )
    
    def get_compensation_response(self) -> str:
        """Get compensation information response."""
        return (
            "Under EU Regulation 261/2004, you may be entitled to compensation "
            "of €250-€600 depending on your flight distance and disruption type:\n\n"
            "• €250 for short-haul flights (under 1,500 km)\n"
            "• €400 for medium-haul flights (1,500 - 3,500 km)\n"
            "• €600 for long-haul flights (over 3,500 km)\n\n"
            "The amount depends on the distance of your flight and the length of the delay. "
            "Would you like to know more about eligibility criteria?"
        )
    
    def get_eligibility_response(self) -> str:
        """Get eligibility criteria response."""
        return (
            "You can claim compensation for:\n\n"
            "• Flight delays over 3 hours at your final destination\n"
            "• Flight cancellations (unless given 14+ days notice)\n"
            "• Denied boarding due to overbooking\n"
            "• Class downgrades\n\n"
            "Exceptions include extraordinary circumstances like bad weather, "
            "security risks, or air traffic control strikes. "
            "The disruption must be within the airline's control."
        )
    
    def get_timeframe_response(self) -> str:
        """Get timeframe information response."""
        return (
            "You can submit a claim up to 3 years after your flight disruption occurred. "
            "However, it's recommended to file your claim as soon as possible while "
            "all the details are fresh and documentation is readily available.\n\n"
            "The processing time for claims typically ranges from a few weeks to several "
            "months, depending on the complexity of the case and the airline's response time."
        )
    
    def get_documents_response(self) -> str:
        """Get required documents response."""
        return (
            "You'll need the following documents for your claim:\n\n"
            "Required:\n"
            "• Boarding pass or e-ticket\n"
            "• Booking confirmation\n"
            "• Any communication from the airline about the disruption\n\n"
            "Helpful (if available):\n"
            "• Receipts for additional expenses\n"
            "• Photos of departure boards showing delays\n"
            "• Written confirmation of the delay from the airline\n\n"
            "You can upload these documents through our file upload system."
        )
    
    def get_status_response(self) -> str:
        """Get claim status response."""
        return (
            "To check your claim status, you can:\n\n"
            "1. Log in to your account using your email and booking reference\n"
            "2. View all your claims and their current status\n"
            "3. Click on any claim to see detailed information and timeline\n\n"
            "Claim statuses include:\n"
            "• Submitted - Your claim has been received\n"
            "• Under Review - We're processing your claim\n"
            "• Approved - Compensation has been approved\n"
            "• Rejected - Claim was rejected (with reason)\n"
            "• Resolved - Claim is complete"
        )
    
    def get_general_response(self) -> str:
        """Get general response for unknown queries."""
        return (
            "I'm here to help with your flight compensation questions. "
            "I can provide information about:\n\n"
            "• Compensation amounts and eligibility\n"
            "• Required documents for your claim\n"
            "• Time limits for submitting claims\n"
            "• How to check your claim status\n\n"
            "Please ask me about any of these topics, or try rephrasing your question."
        )