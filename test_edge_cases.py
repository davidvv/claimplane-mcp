#!/usr/bin/env python3
"""Test edge cases that might cause the email validation issue."""

import asyncio
import httpx
import json
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8001"

async def test_edge_cases():
    """Test edge cases that might cause the email validation issue."""
    print("=== Testing Edge Cases for Email Validation ===")
    
    async with httpx.AsyncClient() as client:
        # Edge Case 1: What if Swagger UI sends email as an empty string?
        print("Edge Case 1: Testing PATCH with empty string email...")
        
        # Create a test customer
        customer_data = {
            "email": f"edge.case1.{uuid4().hex[:8]}@example.com",
            "firstName": "Edge1",
            "lastName": "Case1",
            "phone": "+1234567890"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Created customer with ID: {customer_id}")
        
        # Try PATCH with empty string email
        patch_data_empty_email = {
            "lastName": "UpdatedCase1",
            "email": ""  # Empty string
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_empty_email)
        if response.status_code == 422:
            print("✓ Empty string email correctly rejected with 422 (validation error)")
        elif response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Empty string email handled correctly, lastName updated to: {updated_customer['lastName']}")
        else:
            print(f"✗ Unexpected response: {response.status_code} - {response.text}")
        
        # Edge Case 2: What if Swagger UI sends email as whitespace?
        print("\nEdge Case 2: Testing PATCH with whitespace email...")
        
        patch_data_whitespace_email = {
            "lastName": "UpdatedCase2",
            "email": "   "  # Whitespace only
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_whitespace_email)
        if response.status_code == 422:
            print("✓ Whitespace email correctly rejected with 422")
        else:
            print(f"Response: {response.status_code}")
            if response.status_code == 200:
                print("✓ Whitespace email handled correctly")
        
        # Edge Case 3: What if there are multiple customers with the same email?
        print("\nEdge Case 3: Testing duplicate email creation...")
        
        # Try to create another customer with the same email (should fail)
        duplicate_customer_data = {
            "email": customer_data["email"],  # Same email as first customer
            "firstName": "Duplicate",
            "lastName": "Customer",
            "phone": "+9876543210"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=duplicate_customer_data)
        if response.status_code == 400:
            error_data = response.json()
            if "already exists" in error_data.get("detail", ""):
                print(f"✓ Duplicate email correctly rejected: {error_data['detail']}")
            else:
                print(f"✗ Unexpected error message: {error_data}")
        else:
            print(f"✗ Unexpected response for duplicate email: {response.status_code}")
        
        # Edge Case 4: Test the exact error message format
        print("\nEdge Case 4: Testing exact error message format...")
        
        # Create a customer with a specific email
        specific_email = f"user.exact.{uuid4().hex[:8]}@example.com"
        customer_data_specific = {
            "email": specific_email,
            "firstName": "Exact",
            "lastName": "Test",
            "phone": "+1234567890"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data_specific)
        assert response.status_code == 201
        customer1 = response.json()
        customer1_id = customer1["id"]
        print(f"✓ Created customer 1 with email: {specific_email}")
        
        # Create another customer with different email
        different_email = f"user.different.{uuid4().hex[:8]}@example.com"
        customer_data_different = {
            "email": different_email,
            "firstName": "Different",
            "lastName": "Test",
            "phone": "+9876543210"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data_different)
        assert response.status_code == 201
        customer2 = response.json()
        customer2_id = customer2["id"]
        print(f"✓ Created customer 2 with email: {different_email}")
        
        # Now try to PATCH customer 2 with customer 1's email
        patch_data_conflict = {
            "lastName": "ConflictTest",
            "email": specific_email  # Customer 1's email
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer2_id}", json=patch_data_conflict)
        if response.status_code == 400:
            error_data = response.json()
            error_detail = error_data.get("detail", "")
            print(f"✓ Got expected 400 error: {error_detail}")
            
            # Check if the error message matches the user's exact error
            if "Customer with email" in error_detail and "already exists" in error_detail:
                print("🎯 ERROR MESSAGE MATCHES USER'S EXACT ERROR!")
                print(f"   Error: {error_detail}")
            else:
                print(f"   Error format different from user's: {error_detail}")
        else:
            print(f"✗ Unexpected response: {response.status_code} - {response.text}")

async def main():
    """Run the edge case tests."""
    print("🚀 Testing Edge Cases for Email Validation Issue")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_edge_cases()
        
        print("=" * 60)
        print("🎉 EDGE CASE TESTS COMPLETED! 🎉")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())