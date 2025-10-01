#!/usr/bin/env python3
"""Test script to reproduce the email validation issue."""

import asyncio
import httpx
import json
from datetime import date
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8001"

async def test_email_validation_issue():
    """Test the specific email validation issue."""
    print("=== Testing Email Validation Issue ===")
    
    async with httpx.AsyncClient() as client:
        # First, create a test customer
        customer_data = {
            "email": f"test.email.{uuid4().hex[:8]}@example.com",
            "firstName": "Test",
            "lastName": "User",
            "phone": "+1234567890",
            "address": {
                "street": "123 Test St",
                "city": "Test City",
                "postalCode": "12345",
                "country": "Test Country"
            }
        }
        
        print("Creating test customer...")
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Customer created with ID: {customer_id}")
        print(f"✓ Customer email: {created_customer['email']}")
        
        # Test 1: PATCH with only lastName (should work)
        print("\nTest 1: PATCH with only lastName...")
        patch_data = {
            "lastName": "UpdatedUser"
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Success: lastName updated to '{updated_customer['lastName']}'")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
        
        # Test 2: PATCH with email field included (but same email) - this might trigger the issue
        print("\nTest 2: PATCH with same email included...")
        patch_data_with_email = {
            "lastName": "UpdatedUser2",
            "email": created_customer["email"]  # Same email as existing
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_with_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Success: lastName updated to '{updated_customer['lastName']}' with same email")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
            try:
                error_details = response.json()
                print(f"Error details: {error_details}")
            except:
                print(f"Raw error response: {response.text}")
        
        # Test 3: Create a second customer and try to PATCH first customer with second customer's email
        print("\nTest 3: Creating second customer...")
        customer_data2 = {
            "email": f"test.email2.{uuid4().hex[:8]}@example.com",
            "firstName": "Test2",
            "lastName": "User2",
            "phone": "+9876543210"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data2)
        assert response.status_code == 201, f"Failed to create second customer: {response.text}"
        created_customer2 = response.json()
        customer_id2 = created_customer2["id"]
        print(f"✓ Second customer created with ID: {customer_id2}")
        print(f"✓ Second customer email: {created_customer2['email']}")
        
        # Now try to PATCH first customer with second customer's email (should fail)
        print("\nTest 4: PATCH first customer with second customer's email (should fail)...")
        patch_data_duplicate_email = {
            "lastName": "UpdatedUser3",
            "email": created_customer2["email"]  # Different customer's email
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_duplicate_email)
        if response.status_code == 400:
            error_data = response.json()
            if "already exists" in error_data.get("detail", ""):
                print(f"✓ Correctly rejected duplicate email: {error_data['detail']}")
            else:
                print(f"✗ Unexpected error message: {error_data}")
        else:
            print(f"✗ Unexpected response: {response.status_code} - {response.text}")
        
        # Test 5: Test what Swagger UI might send - check if it includes email field
        print("\nTest 5: Test Swagger UI scenario - PATCH with explicit null email...")
        patch_data_null_email = {
            "lastName": "UpdatedUser4",
            "email": None  # Explicit null email
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_null_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Success: lastName updated to '{updated_customer['lastName']}' with null email")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")

async def main():
    """Run the email validation tests."""
    print("🚀 Starting Email Validation Issue Tests")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_email_validation_issue()
        
        print("=" * 60)
        print("🎉 EMAIL VALIDATION TESTS COMPLETED! 🎉")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())