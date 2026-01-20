from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class SignatureRequest(BaseModel):
    """Request model for signing a Power of Attorney."""
    signature_image: str = Field(..., description="Base64-encoded PNG signature image")
    signer_name: str = Field(..., description="Full name of the signer")
    is_primary_passenger: bool = Field(True, description="Is the signer the primary passenger?")
    consent_terms: bool = Field(..., description="Consent to Terms & Conditions")
    consent_electronic_signature: bool = Field(..., description="Consent to use electronic signatures")
    consent_represent_all: Optional[bool] = Field(None, description="Consent to represent all passengers (multi-passenger only)")

class SignedPOAResponse(BaseModel):
    """Response model for a signed POA."""
    file_id: UUID
    download_url: str
    signed_at: datetime
