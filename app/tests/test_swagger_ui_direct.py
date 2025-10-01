#!/usr/bin/env python3
"""Test script to simulate exact Swagger UI behavior and test the fix."""

import asyncio
import httpx
import json
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8001"

async def test_swagger_ui_direct():
    """Test the exact Swagger UI behavior by sending raw JSON."""
    print("=== Testing Direct Swagger UI Behavior ===")
    
    async with httpx.AsyncClient() as client:
        # Create a test customer
        print("Creating test customer...")
        customer_data = {
            "email": f"swagger.direct.{uuid4().hex[:8]}@example.com",
            "firstName": "Swagger",
            "lastName": "Direct",
            "phone": "+1234567890"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Customer created with ID: {customer_id}")
        
        # Test 1: Simulate Swagger UI sending empty string for email
        print(f"\nTest 1: Simulating Swagger UI with empty string email...")
        
        # This is what Swagger UI might send - a request with empty email field
        swagger_request = {
            "lastName": "UpdatedDirect",
            "email": ""  # Empty string - this should be handled by our fix
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=swagger_request)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Empty string email handled correctly!")
            print(f"  lastName updated to: {updated_customer['lastName']}")
            print(f"  Email remained: {updated_customer['email']}")
        elif response.status_code == 422:
            print(f"✗ Empty string email still causes 422 validation error")
            error_data = response.json()
            print(f"  Error details: {json.dumps(error_data, indent=2)}")
        else:
            print(f"✗ Unexpected response: {response.status_code} - {response.text}")
        
        # Test 2: Simulate Swagger UI sending null for email (should work)
        print(f"\nTest 2: Simulating Swagger UI with null email...")
        
        swagger_request_null = {
            "lastName": "UpdatedDirect2",
            "email": None  # Explicit null
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=swagger_request_null)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Null email handled correctly!")
            print(f"  lastName updated to: {updated_customer['lastName']}")
            print(f"  Email remained: {updated_customer['email']}")
        else:
            print(f"✗ Null email failed: {response.status_code} - {response.text}")
        
        # Test 3: Test with missing email field entirely (ideal PATCH)
        print(f"\nTest 3: Ideal PATCH without email field...")
        
        ideal_patch = {
            "lastName": "UpdatedDirect3"
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=ideal_patch)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Ideal PATCH successful!")
            print(f"  lastName updated to: {updated_customer['lastName']}")
            print(f"  Email remained: {updated_customer['email']}")
        else:
            print(f"✗ Ideal PATCH failed: {response.status_code} - {response.text}")
        
        # Test 4: Test with current email (Swagger UI might send this)
        print(f"\nTest 4: Swagger UI sending current email...")
        
        current_email = updated_customer["email"]
        swagger_current_email = {
            "lastName": "UpdatedDirect4",
            "email": current_email  # Same email as current
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=swagger_current_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Current email handled correctly!")
            print(f"  lastName updated to: {updated_customer['lastName']}")
            print(f"  Email remained: {updated_customer['email']}")
        else:
            print(f"✗ Current email failed: {response.status_code} - {response.text}")

async def main():
    """Run Swagger UI simulation tests."""
    print("🚀 Testing Direct Swagger UI Behavior")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_swagger_ui_direct()
        
        print("=" * 60)
        print("🎉 SWAGGER UI SIMULATION TESTS COMPLETED! 🎉")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())