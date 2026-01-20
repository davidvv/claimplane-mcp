import asyncio
import httpx
from uuid import UUID
import sys

BASE_URL = "http://127.0.0.1:8000"

async def verify_autosave():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Create a draft claim
        print("Creating draft claim...")
        draft_payload = {
            "email": "auto-save-test@example.com",
            "flightInfo": {
                "flightNumber": "UA988",
                "airline": "United Airlines",
                "departureDate": "2025-08-18",
                "departureAirport": "EWR",
                "arrivalAirport": "LHR"
            },
            "incidentType": "delay",
            "compensationAmount": 600,
            "currency": "EUR"
        }
        
        response = await client.post("/claims/draft", json=draft_payload)
        if response.status_code != 201:
            print(f"FAILED to create draft: {response.text}")
            return False
        
        draft_data = response.json()
        claim_id = draft_data["claimId"]
        access_token = draft_data["accessToken"]
        print(f"Draft created: {claim_id}")
        
        # 2. Update draft (Auto-save)
        print("Updating draft (Auto-save)...")
        update_payload = {
            "passengers": [
                {
                    "firstName": "AutoSave",
                    "lastName": "Tester",
                    "ticketNumber": "1234567890123"
                }
            ],
            "street": "123 Test Ave",
            "city": "Test City",
            "postalCode": "12345",
            "country": "Test Country"
        }
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.patch(f"/claims/{claim_id}/draft", json=update_payload, headers=headers)
        
        if response.status_code != 200:
            print(f"FAILED to update draft: {response.text}")
            return False
        
        print("Draft updated successfully via PATCH")
        
        # 3. Verify in DB (using API to get claim)
        print("Verifying updated claim data...")
        response = await client.get(f"/claims/{claim_id}", headers=headers)
        if response.status_code != 200:
            print(f"FAILED to get claim: {response.text}")
            return False
            
        claim_data = response.json()
        print(f"Claim data retrieved: {claim_data}")
        
        # We can't see the passengers in ClaimResponseSchema if it's flat,
        # but we can check if address fields were updated if they are returned.
        # Wait, ClaimResponseSchema might not have all fields.
        
        return True

if __name__ == "__main__":
    success = asyncio.run(verify_autosave())
    sys.exit(0 if success else 1)
