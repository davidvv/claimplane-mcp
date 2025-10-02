#!/usr/bin/env python3
"""
Script to initialize default file validation rules for the flight claim system.
"""

import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings

# Default validation rules
DEFAULT_VALIDATION_RULES = [
    {
        "document_type": "boarding_pass",
        "max_file_size": 5 * 1024 * 1024,  # 5MB
        "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png"],
        "required_file_extensions": [".pdf", ".jpg", ".jpeg", ".png"],
        "max_pages": 2,
        "requires_scan": True,
        "requires_ocr": False,
        "retention_days": 2555,  # 7 years
    },
    {
        "document_type": "id_document",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png"],
        "required_file_extensions": [".pdf", ".jpg", ".jpeg", ".png"],
        "max_pages": 2,
        "requires_scan": True,
        "requires_ocr": False,
        "retention_days": 2555,  # 7 years
    },
    {
        "document_type": "receipt",
        "max_file_size": 2 * 1024 * 1024,  # 2MB
        "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png"],
        "required_file_extensions": [".pdf", ".jpg", ".jpeg", ".png"],
        "max_pages": 5,
        "requires_scan": True,
        "requires_ocr": True,
        "retention_days": 2190,  # 6 years
    },
    {
        "document_type": "bank_statement",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_mime_types": ["application/pdf"],
        "required_file_extensions": [".pdf"],
        "max_pages": 10,
        "requires_scan": True,
        "requires_ocr": True,
        "retention_days": 2555,  # 7 years
    },
    {
        "document_type": "flight_ticket",
        "max_file_size": 5 * 1024 * 1024,  # 5MB
        "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png"],
        "required_file_extensions": [".pdf", ".jpg", ".jpeg", ".png"],
        "max_pages": 3,
        "requires_scan": True,
        "requires_ocr": False,
        "retention_days": 2555,  # 7 years
    },
    {
        "document_type": "delay_certificate",
        "max_file_size": 5 * 1024 * 1024,  # 5MB
        "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png"],
        "required_file_extensions": [".pdf", ".jpg", ".jpeg", ".png"],
        "max_pages": 2,
        "requires_scan": True,
        "requires_ocr": True,
        "retention_days": 2555,  # 7 years
    },
    {
        "document_type": "cancellation_notice",
        "max_file_size": 5 * 1024 * 1024,  # 5MB
        "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png"],
        "required_file_extensions": [".pdf", ".jpg", ".jpeg", ".png"],
        "max_pages": 2,
        "requires_scan": True,
        "requires_ocr": True,
        "retention_days": 2555,  # 7 years
    },
    {
        "document_type": "other",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        "required_file_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"],
        "max_pages": 20,
        "requires_scan": True,
        "requires_ocr": False,
        "retention_days": 1095,  # 3 years
    },
]

async def init_file_validation_rules():
    """Initialize default file validation rules in the database."""
    try:
        # Create engine
        engine = create_async_engine(settings.DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            print("Initializing file validation rules...")
            
            # Check if rules already exist
            result = await conn.execute(
                text("SELECT COUNT(*) FROM file_validation_rules")
            )
            count = result.scalar()
            
            if count > 0:
                print(f"✅ File validation rules already exist ({count} rules found)")
                return
            
            # Insert default rules
            for rule in DEFAULT_VALIDATION_RULES:
                await conn.execute(
                    text("""
                        INSERT INTO file_validation_rules (
                            id, document_type, max_file_size, allowed_mime_types,
                            required_file_extensions, max_pages, requires_ocr,
                            requires_scan, retention_days, is_active, priority
                        ) VALUES (
                            gen_random_uuid(), :document_type, :max_file_size, :allowed_mime_types,
                            :required_file_extensions, :max_pages, :requires_ocr,
                            :requires_scan, :retention_days, 1, 100
                        )
                    """),
                    {
                        "document_type": rule["document_type"],
                        "max_file_size": rule["max_file_size"],
                        "allowed_mime_types": json.dumps(rule["allowed_mime_types"]),
                        "required_file_extensions": json.dumps(rule["required_file_extensions"]),
                        "max_pages": rule["max_pages"],
                        "requires_ocr": rule["requires_ocr"],
                        "requires_scan": rule["requires_scan"],
                        "retention_days": rule["retention_days"],
                    }
                )
            
            print("✅ File validation rules initialized successfully!")
            
    except Exception as e:
        print(f"❌ Error initializing file validation rules: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_file_validation_rules())