#!/usr/bin/env python3
"""Test script to reproduce the exact Swagger UI scenario."""

import asyncio
import httpx
import json
from datetime import date
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8001"

async def test_swagger_ui_exact_scenario():
    """Test the exact scenario that might cause the issue."""
    print("=== Testing Exact Swagger UI Scenario ===")
    
    async with httpx.AsyncClient() as client:
        # First, create a test customer
        customer_data = {
            "email": f"swagger.user.{uuid4().hex[:8]}@example.com",
            "firstName": "Swagger",
            "lastName": "User",
            "phone": "+1234567890",
            "address": {
                "street": "123 Swagger St",
                "city": "Swagger City",
                "postalCode": "12345",
                "country": "Swagger Country"
            }
        }
        
        print("Creating test customer...")
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Customer created with ID: {customer_id}")
        print(f"✓ Customer email: {created_customer['email']}")
        
        # Test what Swagger UI might send - let's simulate different scenarios
        print("\n=== Simulating Swagger UI Request Scenarios ===")
        
        # Scenario 1: Swagger UI sends all fields (including email) even for PATCH
        print("\nScenario 1: Swagger UI sends all fields including email...")
        swagger_request_data = {
            "email": created_customer["email"],  # Same email
            "firstName": created_customer["firstName"],  # Same firstName
            "lastName": "johanson",  # Only this should change
            "phone": created_customer["phone"],  # Same phone
            "address": created_customer["address"]  # Same address
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=swagger_request_data)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Success: lastName updated to '{updated_customer['lastName']}'")
            print(f"✓ Email remained: {updated_customer['email']}")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
        
        # Scenario 2: Swagger UI sends email as empty string (potential issue)
        print("\nScenario 2: Swagger UI sends email as empty string...")
        swagger_request_data_empty_email = {
            "email": "",  # Empty string email
            "lastName": "johanson2"
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=swagger_request_data_empty_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Success: lastName updated to '{updated_customer['lastName']}'")
            print(f"✓ Email: {updated_customer['email']}")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
            try:
                error_details = response.json()
                print(f"Error details: {error_details}")
            except:
                print(f"Raw error response: {response.text}")
        
        # Scenario 3: Swagger UI sends email field but it's null (this might be the issue)
        print("\nScenario 3: Swagger UI sends email as null...")
        swagger_request_data_null_email = {
            "email": None,  # Explicit null
            "lastName": "johanson3"
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=swagger_request_data_null_email)
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"✓ Success: lastName updated to '{updated_customer['lastName']}'")
            print(f"✓ Email: {updated_customer['email']}")
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
        
        # Scenario 4: Check what happens if we have a customer with email "user@example.com"
        print("\nScenario 4: Create customer with exact email from user's error...")
        customer_data_exact_email = {
            "email": "user@example.com",
            "firstName": "Test",
            "lastName": "User",
            "phone": "+1234567890"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data_exact_email)
        if response.status_code == 201:
            created_customer_exact = response.json()
            customer_id_exact = created_customer_exact["id"]
            print(f"✓ Customer created with email 'user@example.com' and ID: {customer_id_exact}")
            
            # Now try to PATCH this customer with only lastName
            print("\nTesting PATCH on customer with email 'user@example.com'...")
            patch_data_exact = {
                "lastName": "johanson"
            }
            
            response = await client.patch(f"{BASE_URL}/customers/{customer_id_exact}", json=patch_data_exact)
            if response.status_code == 200:
                updated_customer_exact = response.json()
                print(f"✓ Success: lastName updated to '{updated_customer_exact['lastName']}'")
                print(f"✓ Email remained: {updated_customer_exact['email']}")
            else:
                print(f"✗ Failed: {response.status_code} - {response.text}")
                try:
                    error_details = response.json()
                    print(f"Error details: {error_details}")
                except:
                    print(f"Raw error response: {response.text}")
        else:
            print(f"✗ Could not create customer with email 'user@example.com': {response.status_code} - {response.text}")

async def main():
    """Run the exact Swagger UI scenario tests."""
    print("🚀 Testing Exact Swagger UI Scenarios")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_swagger_ui_exact_scenario()
        
        print("=" * 60)
        print("🎉 EXACT SCENARIO TESTS COMPLETED! 🎉")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())