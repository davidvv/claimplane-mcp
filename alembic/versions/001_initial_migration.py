"""Initial migration - create all tables.

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('booking_reference', sa.String(length=255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_user_email_booking', 'users', ['email', 'booking_reference'])
    
    # Create claims table
    op.create_table(
        'claims',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('booking_reference', sa.String(length=255), nullable=False),
        sa.Column('flight_number', sa.String(length=10), nullable=False),
        sa.Column('planned_departure_date', sa.Date(), nullable=False),
        sa.Column('actual_departure_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disruption_type', sa.String(length=50), nullable=True),
        sa.Column('incident_description', sa.Text(), nullable=True),
        sa.Column('declaration_accepted', sa.Boolean(), nullable=False),
        sa.Column('consent_accepted', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('claim_id')
    )
    op.create_index('idx_claims_user_id', 'claims', ['user_id'])
    op.create_index('idx_claims_email', 'claims', ['email'])
    op.create_index('idx_claims_booking_reference', 'claims', ['booking_reference'])
    op.create_index('idx_claims_flight_number', 'claims', ['flight_number'])
    op.create_index('idx_claims_status', 'claims', ['status'])
    op.create_index('idx_claims_created_at', 'claims', ['created_at'])
    op.create_index('idx_claim_email_booking', 'claims', ['email', 'booking_reference'])
    op.create_index('idx_claim_status_created', 'claims', ['status', 'created_at'])
    
    # Add flight number format constraint
    op.create_check_constraint(
        'valid_flight_number_format',
        'claims',
        "flight_number ~ '^[A-Z]{2}\\d{3,4}$'"
    )
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documents_claim_id', 'documents', ['claim_id'])
    op.create_index('idx_document_claim_type', 'documents', ['claim_id', 'document_type'])
    
    # Create claim_status_history table
    op.create_table(
        'claim_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('claim_id', sa.Integer(), nullable=False),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('changed_by', sa.String(length=255), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_status_history_claim', 'claim_status_history', ['claim_id', 'changed_at'])
    
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('idx_chat_sessions_session_id', 'chat_sessions', ['session_id'])
    op.create_index('idx_chat_session_user', 'chat_sessions', ['user_id', 'created_at'])
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('sender', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('idx_chat_message_session_time', 'chat_messages', ['session_id', 'created_at'])
    
    # Add sender type constraint
    op.create_check_constraint(
        'valid_sender_type',
        'chat_messages',
        "sender IN ('user', 'bot')"
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('claim_status_history')
    op.drop_table('documents')
    op.drop_table('claims')
    op.drop_table('users')