#!/usr/bin/env python3
"""Test script to verify the PATCH fix handles empty string emails correctly."""

import asyncio
import httpx
import json
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8001"

async def test_fix_verification():
    """Test that the fix properly handles empty string emails."""
    print("=== Verifying PATCH Fix for Empty String Emails ===")
    
    async with httpx.AsyncClient() as client:
        # Create a test customer
        print("Creating test customer...")
        customer_data = {
            "email": f"fix.test.{uuid4().hex[:8]}@example.com",
            "firstName": "Fix",
            "lastName": "Test",
            "phone": "+1234567890"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Customer created with ID: {customer_id}")
        
        # Test 1: PATCH with empty string email (should be ignored, not cause 422)
        print(f"\nTest 1: PATCH with empty string email...")
        patch_data_empty_email = {
            "lastName": "UpdatedTest",
            "email": ""  # Empty string - should be ignored by our fix
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_empty_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Empty string email handled correctly!")
            print(f"  lastName updated to: {updated_customer['lastName']}")
            print(f"  Email remained: {updated_customer['email']}")
        elif response.status_code == 422:
            print(f"✗ Empty string email still causes 422 validation error")
            error_data = response.json()
            print(f"  Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
        else:
            print(f"✗ Unexpected response: {response.status_code} - {response.text}")
        
        # Test 2: PATCH with whitespace-only email (should be ignored)
        print(f"\nTest 2: PATCH with whitespace-only email...")
        patch_data_whitespace_email = {
            "lastName": "UpdatedTest2",
            "email": "   "  # Whitespace only - should be ignored by our fix
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_whitespace_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Whitespace-only email handled correctly!")
            print(f"  lastName updated to: {updated_customer['lastName']}")
            print(f"  Email remained: {updated_customer['email']}")
        elif response.status_code == 422:
            print(f"✗ Whitespace-only email still causes 422 validation error")
            error_data = response.json()
            print(f"  Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
        else:
            print(f"✗ Unexpected response: {response.status_code} - {response.text}")
        
        # Test 3: PATCH with same email (case insensitive test)
        print(f"\nTest 3: PATCH with same email (case test)...")
        original_email = created_customer["email"]
        upper_case_email = original_email.upper()  # Same email but uppercase
        
        patch_data_case_email = {
            "lastName": "UpdatedTest3",
            "email": upper_case_email  # Same email, different case
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_case_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Case-insensitive email comparison works!")
            print(f"  lastName updated to: {updated_customer['lastName']}")
            print(f"  Email remained: {updated_customer['email']}")
        else:
            print(f"✗ Case-insensitive test failed: {response.status_code} - {response.text}")
        
        # Test 4: PATCH with actual email change (should work if email is unique)
        print(f"\nTest 4: PATCH with actual email change...")
        new_email = f"new.email.{uuid4().hex[:8]}@example.com"
        
        patch_data_new_email = {
            "lastName": "UpdatedTest4",
            "email": new_email
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_new_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Email change successful!")
            print(f"  lastName updated to: {updated_customer['lastName']}")
            print(f"  Email changed to: {updated_customer['email']}")
        else:
            print(f"✗ Email change failed: {response.status_code} - {response.text}")
        
        # Test 5: PATCH with duplicate email (should fail)
        print(f"\nTest 5: PATCH with duplicate email (should fail)...")
        # Create another customer first
        other_customer_data = {
            "email": f"other.test.{uuid4().hex[:8]}@example.com",
            "firstName": "Other",
            "lastName": "Test",
            "phone": "+9876543210"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=other_customer_data)
        assert response.status_code == 201
        other_customer = response.json()
        other_email = other_customer["email"]
        print(f"✓ Created other customer with email: {other_email}")
        
        # Now try to PATCH our main customer with the other customer's email
        patch_data_duplicate_email = {
            "lastName": "UpdatedTest5",
            "email": other_email  # This should fail
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_duplicate_email)
        if response.status_code == 400:
            error_data = response.json()
            if "already exists" in error_data.get("detail", ""):
                print(f"✓ Duplicate email correctly rejected!")
                print(f"  Error: {error_data['detail']}")
            else:
                print(f"✗ Unexpected error message: {error_data}")
        else:
            print(f"✗ Unexpected response for duplicate email: {response.status_code} - {response.text}")

async def main():
    """Run fix verification tests."""
    print("🚀 Testing PATCH Fix for Empty String Email Issues")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_fix_verification()
        
        print("=" * 60)
        print("🎉 FIX VERIFICATION COMPLETED! 🎉")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())