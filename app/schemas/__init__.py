"""Pydantic schemas for request/response validation."""

# Import all schemas from the parent module's schemas.py file
import sys
import importlib.util
from pathlib import Path

# Load the schemas.py file from parent directory (using relative path)
schemas_path = Path(__file__).parent.parent / "schemas.py"
spec = importlib.util.spec_from_file_location("app_schemas", str(schemas_path))
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)

# Export all schemas from schemas.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Union
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator

# Re-export all classes from schemas.py
AddressSchema = schemas_module.AddressSchema
CustomerCreateSchema = schemas_module.CustomerCreateSchema
CustomerUpdateSchema = schemas_module.CustomerUpdateSchema
CustomerPatchSchema = schemas_module.CustomerPatchSchema
CustomerResponseSchema = schemas_module.CustomerResponseSchema
HealthResponseSchema = schemas_module.HealthResponseSchema
FlightInfoSchema = schemas_module.FlightInfoSchema
ClaimCreateSchema = schemas_module.ClaimCreateSchema
ClaimUpdateSchema = schemas_module.ClaimUpdateSchema
ClaimPatchSchema = schemas_module.ClaimPatchSchema
ClaimResponseSchema = schemas_module.ClaimResponseSchema
ClaimRequestSchema = schemas_module.ClaimRequestSchema
ClaimSubmitResponseSchema = schemas_module.ClaimSubmitResponseSchema
ClaimDraftSchema = schemas_module.ClaimDraftSchema
ClaimDraftResponseSchema = schemas_module.ClaimDraftResponseSchema
ClaimDraftUpdateSchema = schemas_module.ClaimDraftUpdateSchema
FileUploadSchema = schemas_module.FileUploadSchema
FileResponseSchema = schemas_module.FileResponseSchema
FileListResponseSchema = schemas_module.FileListResponseSchema
FileAccessLogSchema = schemas_module.FileAccessLogSchema
FileSearchSchema = schemas_module.FileSearchSchema
FileValidationRuleSchema = schemas_module.FileValidationRuleSchema
FileSummarySchema = schemas_module.FileSummarySchema
ErrorResponseSchema = schemas_module.ErrorResponseSchema

# Import OCR schemas from local module
from app.schemas.ocr_schemas import (
    BoardingPassDataSchema,
    FieldConfidenceSchema,
    OCRResponseSchema,
)

__all__ = [
    "AddressSchema",
    "CustomerCreateSchema",
    "CustomerUpdateSchema",
    "CustomerPatchSchema",
    "CustomerResponseSchema",
    "HealthResponseSchema",
    "FlightInfoSchema",
    "ClaimCreateSchema",
    "ClaimUpdateSchema",
    "ClaimPatchSchema",
    "ClaimResponseSchema",
    "ClaimRequestSchema",
    "ClaimSubmitResponseSchema",
    "ClaimDraftSchema",
    "ClaimDraftResponseSchema",
    "ClaimDraftUpdateSchema",
    "FileUploadSchema",
    "FileResponseSchema",
    "FileListResponseSchema",
    "FileAccessLogSchema",
    "FileSearchSchema",
    "FileValidationRuleSchema",
    "FileSummarySchema",
    "ErrorResponseSchema",
    # OCR schemas
    "BoardingPassDataSchema",
    "FieldConfidenceSchema",
    "OCRResponseSchema",
]
