#!/usr/bin/env python3
"""Test script to reproduce the exact issue the user is experiencing."""

import asyncio
import httpx
import json
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8001"

async def test_reproduce_exact_issue():
    """Reproduce the exact issue: Customer with email user@example.com already exists."""
    print("=== Reproducing Exact User Issue ===")
    
    async with httpx.AsyncClient() as client:
        # First, let's see if there's already a customer with email "user@example.com"
        print("Checking if customer with email 'user@example.com' exists...")
        response = await client.get(f"{BASE_URL}/customers/search/by-email/user@example.com")
        
        if response.status_code == 200:
            existing_customers = response.json()
            if existing_customers:
                print(f"✓ Found existing customer(s) with email 'user@example.com'")
                for customer in existing_customers:
                    print(f"  - Customer ID: {customer['id']}, Name: {customer['firstName']} {customer['lastName']}")
            else:
                print("✗ No customer found with email 'user@example.com'")
                return
        else:
            print(f"✗ Error checking for existing customer: {response.status_code}")
            return
        
        # Now create a new customer with a different email
        print("\nCreating a new test customer...")
        customer_data = {
            "email": f"test.issue.{uuid4().hex[:8]}@example.com",
            "firstName": "Test",
            "lastName": "Issue",
            "phone": "+1234567890"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ New customer created with ID: {customer_id}")
        print(f"✓ New customer email: {created_customer['email']}")
        
        # Now try to PATCH this new customer with only lastName, but simulate what Swagger UI might do
        # Swagger UI might send the current email value along with the changed field
        print(f"\nTesting PATCH on new customer (ID: {customer_id})...")
        print("Simulating Swagger UI request that includes current email value...")
        
        # This is what might be causing the issue - Swagger UI sends current email value
        patch_data_with_current_email = {
            "lastName": "johanson",  # Only this should change
            "email": created_customer["email"]  # Swagger UI might send current email
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_with_current_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Success: lastName updated to '{updated_customer['lastName']}'")
            print(f"✓ Email remained unchanged: {updated_customer['email']}")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
            try:
                error_details = response.json()
                print(f"Error details: {error_details}")
                if "already exists" in str(error_details):
                    print("🎯 FOUND THE ISSUE! Email validation is incorrectly triggering!")
            except:
                print(f"Raw error response: {response.text}")
        
        # Now test the problematic scenario: try to PATCH with an email that belongs to another customer
        print(f"\nTesting problematic scenario - PATCH with another customer's email...")
        # Get the first customer with "user@example.com" email
        response = await client.get(f"{BASE_URL}/customers/search/by-email/user@example.com")
        if response.status_code == 200:
            existing_customers = response.json()
            if existing_customers:
                existing_customer = existing_customers[0]  # Take the first one
                existing_customer_id = existing_customer['id']
                existing_customer_email = existing_customer['email']
                
                print(f"Found existing customer: ID={existing_customer_id}, Email={existing_customer_email}")
                
                # Now try to PATCH our new customer with the existing customer's email
                print("Attempting to PATCH new customer with existing customer's email...")
                problematic_patch_data = {
                    "lastName": "johanson2",
                    "email": existing_customer_email  # This should trigger the error
                }
                
                response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=problematic_patch_data)
                if response.status_code == 400:
                    error_data = response.json()
                    if "already exists" in error_data.get("detail", ""):
                        print(f"✓ Correctly rejected: {error_data['detail']}")
                        print("This is the expected behavior - email validation working correctly")
                    else:
                        print(f"✗ Unexpected error: {error_data}")
                else:
                    print(f"✗ Unexpected response: {response.status_code} - {response.text}")
            else:
                print("✗ No existing customer found with 'user@example.com' email")
        else:
            print(f"✗ Error finding existing customer: {response.status_code}")

async def main():
    """Run the exact issue reproduction test."""
    print("🚀 Reproducing Exact User Issue")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_reproduce_exact_issue()
        
        print("=" * 60)
        print("🎉 ISSUE REPRODUCTION TEST COMPLETED! 🎉")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())