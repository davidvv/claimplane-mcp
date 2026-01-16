
import asyncio
import os
from fastapi import UploadFile
from app.database import AsyncSessionLocal
from app.services.file_service import get_file_service

async def upload_boarding_pass():
    claim_id = "123e2568-ddc2-495d-bf31-540aad0b59c2"
    customer_id = "7e6fba2f-ff70-4c71-b05a-47364249c54a"
    file_path = "/app/app/tests/fixtures/boarding_passes/Boarding_MUC-MAD.png"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    print(f"🚀 Starting upload for Claim {claim_id}...")
    
    async with AsyncSessionLocal() as db:
        file_service = get_file_service(db)
        
        # Open file in binary mode
        with open(file_path, "rb") as f:
            # Create UploadFile object (FastAPI wrapper)
            upload_file = UploadFile(
                filename="Boarding_MUC-MAD.png",
                file=f,
                headers={"content-type": "image/png"}
            )
            
            try:
                result = await file_service.upload_file(
                    file=upload_file,
                    claim_id=claim_id,
                    customer_id=customer_id,
                    document_type="boarding_pass",
                    description="Boarding Pass (MUC-MAD) - Auto-uploaded test file",
                    access_level="private"
                )
                await db.commit()  # Explicitly commit the transaction
                print(f"✅ Upload Successful!")
                print(f"File ID: {result.id}")
                print(f"Path: {result.storage_path}")
            except Exception as e:
                print(f"❌ Upload Failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(upload_boarding_pass())
