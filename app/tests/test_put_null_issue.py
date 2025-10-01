#!/usr/bin/env python3
"""Test script to reproduce the PUT null reset issue."""

import asyncio
import httpx
import json
from datetime import date
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8000"

async def test_put_null_reset_issue():
    """Test to reproduce the PUT null reset issue."""
    print("=== Testing PUT Null Reset Issue ===")
    
    async with httpx.AsyncClient() as client:
        # First, create a test customer with all fields
        customer_data = {
            "email": f"test.customer.{uuid4().hex[:8]}@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "phone": "+1234567890",
            "address": {
                "street": "123 Test St",
                "city": "Test City",
                "postalCode": "12345",
                "country": "Test Country"
            }
        }
        
        print("Creating test customer with all fields...")
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Customer created with ID: {customer_id}")
        print(f"  Phone: {created_customer.get('phone')}")
        print(f"  Address: {created_customer.get('address')}")
        
        # Test 1: PUT with phone set to None (should reset to null)
        print("\nTest 1: PUT with phone explicitly set to null...")
        put_data_with_null_phone = {
            "email": f"updated.{uuid4().hex[:8]}@example.com",
            "firstName": "Jane",
            "lastName": "Smith",
            "phone": None,  # Explicitly set to None
            "address": {
                "street": "456 Updated St",
                "city": "Updated City",
                "postalCode": "54321",
                "country": "Updated Country"
            }
        }
        
        response = await client.put(f"{BASE_URL}/customers/{customer_id}", json=put_data_with_null_phone)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"  Updated phone: {updated_customer.get('phone')}")
            print(f"  Expected: None")
            if updated_customer.get('phone') is None:
                print("  ✓ Phone was correctly set to null")
            else:
                print("  ❌ Phone was not set to null - this indicates the issue!")
        
        # Test 2: PUT with missing phone field (what happens?)
        print("\nTest 2: PUT with missing phone field...")
        put_data_missing_phone = {
            "email": f"updated2.{uuid4().hex[:8]}@example.com",
            "firstName": "Janet",
            "lastName": "Johnson",
            # phone field is missing
            "address": {
                "street": "789 Another St",
                "city": "Another City",
                "postalCode": "98765",
                "country": "Another Country"
            }
        }
        
        response = await client.put(f"{BASE_URL}/customers/{customer_id}", json=put_data_missing_phone)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            updated_customer = response.json()
            print(f"  Updated phone: {updated_customer.get('phone')}")
            print(f"  Expected: Should be null or previous value?")
            # According to REST, PUT should replace the entire resource
            # So missing fields should be set to their default values (null for optional fields)
        
        # Test 3: Check what the current behavior is
        print("\nTest 3: Checking current customer state...")
        response = await client.get(f"{BASE_URL}/customers/{customer_id}")
        if response.status_code == 200:
            current_customer = response.json()
            print(f"  Current phone: {current_customer.get('phone')}")
            print(f"  Current email: {current_customer.get('email')}")
            print(f"  Current firstName: {current_customer.get('firstName')}")
            print(f"  Current lastName: {current_customer.get('lastName')}")

async def test_claim_put_null_issue():
    """Test claim PUT null reset issue."""
    print("\n=== Testing Claim PUT Null Reset Issue ===")
    
    async with httpx.AsyncClient() as client:
        # Create test customer
        customer_data = {
            "email": f"claim.test.{uuid4().hex[:8]}@example.com",
            "firstName": "Claim",
            "lastName": "Tester",
            "phone": "+1234567890"
        }
        
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201
        created_customer = response.json()
        customer_id = created_customer["id"]
        
        # Create claim with notes
        claim_data = {
            "customerId": customer_id,
            "flightInfo": {
                "flightNumber": "LH123",
                "airline": "Lufthansa",
                "departureDate": str(date.today()),
                "departureAirport": "FRA",
                "arrivalAirport": "JFK"
            },
            "incidentType": "delay",
            "notes": "Flight delayed by 3 hours"
        }
        
        response = await client.post(f"{BASE_URL}/claims/", json=claim_data)
        assert response.status_code == 201
        created_claim = response.json()
        claim_id = created_claim["id"]
        print(f"✓ Claim created with ID: {claim_id}")
        print(f"  Notes: {created_claim.get('notes')}")
        
        # Test PUT with notes set to None
        print("\nTest: PUT with notes set to null...")
        put_data_with_null_notes = {
            "customerId": customer_id,
            "flightInfo": {
                "flightNumber": "BA456",
                "airline": "British Airways",
                "departureDate": str(date.today()),
                "departureAirport": "LHR",
                "arrivalAirport": "CDG"
            },
            "incidentType": "cancellation",
            "notes": None  # Explicitly set to None
        }
        
        response = await client.put(f"{BASE_URL}/claims/{claim_id}", json=put_data_with_null_notes)
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            updated_claim = response.json()
            print(f"  Updated notes: {updated_claim.get('notes')}")
            print(f"  Expected: None")
            if updated_claim.get('notes') is None:
                print("  ✓ Notes was correctly set to null")
            else:
                print("  ❌ Notes was not set to null - this indicates the issue!")

async def main():
    """Run the tests."""
    print("Testing PUT null reset issue...")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_put_null_reset_issue()
        await test_claim_put_null_issue()
        
        print("\n" + "=" * 60)
        print("Test completed. Check the results above to identify the issue.")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())