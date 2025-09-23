"""SQLAlchemy models for the Flight Compensation Claim API."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Date, 
    CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """User model for authentication and claim association."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    booking_reference = Column(String(255), nullable=False, index=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    claims = relationship("Claim", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    
    __table_args__ = (
        Index("idx_user_email_booking", "email", "booking_reference"),
    )


class Claim(Base):
    """Claim model storing all claim data."""
    
    __tablename__ = "claims"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Personal Information (from PersonalInfo schema)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    booking_reference = Column(String(255), nullable=False, index=True)
    
    # Flight Details (from FlightDetails schema)
    flight_number = Column(String(10), nullable=False, index=True)
    planned_departure_date = Column(Date, nullable=False, index=True)
    actual_departure_time = Column(DateTime(timezone=True), nullable=True)
    
    # Additional claim details
    disruption_type = Column(String(50), nullable=True)
    incident_description = Column(Text, nullable=True)
    
    # Legal declarations
    declaration_accepted = Column(Boolean, default=False, nullable=False)
    consent_accepted = Column(Boolean, default=False, nullable=False)
    
    # Status tracking
    status = Column(String(50), default="submitted", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="claims")
    documents = relationship("Document", back_populates="claim", cascade="all, delete-orphan")
    status_history = relationship("ClaimStatusHistory", back_populates="claim", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            "flight_number ~ '^[A-Z]{2}\\d{3,4}$'",
            name="valid_flight_number_format"
        ),
        Index("idx_claim_email_booking", "email", "booking_reference"),
        Index("idx_claim_status_created", "status", "created_at"),
    )


class Document(Base):
    """Document model for file uploads."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(50), nullable=False, index=True)  # 'boarding_pass', 'receipt', etc.
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    claim = relationship("Claim", back_populates="documents")
    
    __table_args__ = (
        Index("idx_document_claim_type", "claim_id", "document_type"),
    )


class ClaimStatusHistory(Base):
    """Claim status history for audit trail."""
    
    __tablename__ = "claim_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False, index=True)
    changed_by = Column(String(255), nullable=True)  # Could be user ID or 'system'
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
    
    # Relationships
    claim = relationship("Claim", back_populates="status_history")
    
    __table_args__ = (
        Index("idx_status_history_claim", "claim_id", "changed_at"),
    )


class ChatSession(Base):
    """Chat session model for chatbot functionality."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_chat_session_user", "user_id", "created_at"),
    )


class ChatMessage(Base):
    """Chat message model for chatbot functionality."""
    
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("chat_sessions.session_id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    sender = Column(String(20), nullable=False)  # 'user' or 'bot'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    __table_args__ = (
        CheckConstraint("sender IN ('user', 'bot')", name="valid_sender_type"),
        Index("idx_chat_message_session_time", "session_id", "created_at"),
    )