#!/usr/bin/env python3
"""Test script to simulate Swagger UI PATCH issues."""

import asyncio
import httpx
import json
from datetime import date
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8001"

async def test_swagger_ui_field_naming():
    """Test different field naming conventions that Swagger UI might use."""
    print("=== Testing Swagger UI Field Naming Issues ===")
    
    async with httpx.AsyncClient() as client:
        # First, create a test customer
        customer_data = {
            "email": f"swagger.test.{uuid4().hex[:8]}@example.com",
            "firstName": "Swagger",
            "lastName": "Test",
            "phone": "+1234567890",
            "address": {
                "street": "123 UI St",
                "city": "UI City",
                "postalCode": "12345",
                "country": "UI Country"
            }
        }
        
        print("Creating test customer...")
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Customer created with ID: {customer_id}")
        
        # Test 1: Swagger UI camelCase format (what OpenAPI spec shows)
        print("\nTest 1: Swagger UI camelCase format...")
        patch_data_camel = {
            "lastName": "johanson"
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_camel)
        if response.status_code == 200:
            updated_customer = response.json()
            if updated_customer["lastName"] == "johanson":
                print("✓ Swagger UI camelCase format works")
            else:
                print("✗ Swagger UI camelCase format failed - surname not updated")
        else:
            print(f"✗ Swagger UI camelCase format failed: {response.status_code} - {response.text}")
        
        # Test 2: Mixed case - some camelCase, some snake_case
        print("\nTest 2: Mixed case format...")
        patch_data_mixed = {
            "lastName": "johanson2",
            "phone": "+9876543210"
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_mixed)
        if response.status_code == 200:
            updated_customer = response.json()
            if updated_customer["lastName"] == "johanson2" and updated_customer["phone"] == "+9876543210":
                print("✓ Mixed case format works")
            else:
                print("✗ Mixed case format failed - fields not updated correctly")
        else:
            print(f"✗ Mixed case format failed: {response.status_code} - {response.text}")
        
        # Test 3: Empty request (Swagger UI might send this)
        print("\nTest 3: Empty request...")
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json={})
        if response.status_code == 200:
            print("✓ Empty request works")
        else:
            print(f"✗ Empty request failed: {response.status_code} - {response.text}")
        
        # Test 4: Null values (Swagger UI might send nulls)
        print("\nTest 4: Null values...")
        patch_data_nulls = {
            "phone": None,
            "lastName": "johanson3"
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_nulls)
        if response.status_code == 200:
            updated_customer = response.json()
            if updated_customer["lastName"] == "johanson3":
                print("✓ Null values handled correctly")
            else:
                print("✗ Null values not handled correctly")
        else:
            print(f"✗ Null values failed: {response.status_code} - {response.text}")
        
        print("\n=== Field Naming Tests Completed ===\n")

async def test_swagger_ui_request_issues():
    """Test various request issues that Swagger UI might encounter."""
    print("=== Testing Swagger UI Request Issues ===")
    
    async with httpx.AsyncClient() as client:
        # Use existing customer
        customer_id = "cfafc71f-9f9a-4b6c-a9bd-360a821c14c7"
        
        # Test 1: Invalid JSON (malformed request)
        print("\nTest 1: Invalid JSON...")
        try:
            response = await client.patch(
                f"{BASE_URL}/customers/{customer_id}",
                content="invalid json {",
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 422:
                print("✓ Invalid JSON properly rejected with 422")
            else:
                print(f"✗ Invalid JSON not handled correctly: {response.status_code}")
        except Exception as e:
            print(f"✗ Invalid JSON test failed: {e}")
        
        # Test 2: Wrong Content-Type
        print("\nTest 2: Wrong Content-Type...")
        response = await client.patch(
            f"{BASE_URL}/customers/{customer_id}",
            data="lastName=johanson",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 422:
            print("✓ Wrong Content-Type properly rejected")
        else:
            print(f"✗ Wrong Content-Type not handled correctly: {response.status_code}")
        
        # Test 3: Valid request for comparison
        print("\nTest 3: Valid request for comparison...")
        response = await client.patch(
            f"{BASE_URL}/customers/{customer_id}",
            json={"lastName": "johanson4"}
        )
        if response.status_code == 200:
            updated_customer = response.json()
            if updated_customer["lastName"] == "johanson4":
                print("✓ Valid request works correctly")
            else:
                print("✗ Valid request didn't update correctly")
        else:
            print(f"✗ Valid request failed: {response.status_code} - {response.text}")
        
        print("\n=== Request Issues Tests Completed ===\n")

async def test_swagger_ui_specific_scenario():
    """Test the exact scenario the user reported."""
    print("=== Testing User's Specific Scenario ===")
    
    async with httpx.AsyncClient() as client:
        # Use the exact customer ID the user mentioned
        customer_id = "cfafc71f-9f9a-4b6c-a9bd-360a821c14c7"
        
        print(f"Testing PATCH for customer ID: {customer_id}")
        
        # Get current customer data first
        response = await client.get(f"{BASE_URL}/customers/{customer_id}")
        if response.status_code == 200:
            current_customer = response.json()
            print(f"Current surname: {current_customer['lastName']}")
        else:
            print(f"✗ Could not get customer: {response.status_code}")
            return
        
        # Test the exact PATCH request the user tried
        print("\nTesting surname change to 'johanson'...")
        patch_data = {
            "lastName": "johanson"
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data)
        if response.status_code == 200:
            updated_customer = response.json()
            if updated_customer["lastName"] == "johanson":
                print("✓ Surname successfully changed to 'johanson'")
                print(f"✓ Updated timestamp: {updated_customer['updatedAt']}")
            else:
                print(f"✗ Surname not updated. Expected 'johanson', got '{updated_customer['lastName']}'")
        else:
            print(f"✗ PATCH request failed: {response.status_code} - {response.text}")
            # Try to get more details about the error
            try:
                error_details = response.json()
                print(f"Error details: {error_details}")
            except:
                print(f"Raw error response: {response.text}")
        
        print("\n=== User Scenario Test Completed ===\n")

async def main():
    """Run all Swagger UI simulation tests."""
    print("🚀 Starting Swagger UI PATCH Issue Simulation Tests")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_swagger_ui_specific_scenario()
        await test_swagger_ui_field_naming()
        await test_swagger_ui_request_issues()
        
        print("=" * 60)
        print("🎉 ALL SWAGGER UI SIMULATION TESTS COMPLETED! 🎉")
        print("If all tests passed, the API is working correctly.")
        print("The issue might be in the Swagger UI JavaScript/client-side.")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())