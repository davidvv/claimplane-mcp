#!/usr/bin/env python3
"""Test script for PUT and PATCH endpoints."""

import asyncio
import httpx
import json
from datetime import date
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8000"

async def test_customer_update_endpoints():
    """Test customer PUT and PATCH endpoints."""
    print("=== Testing Customer Update Endpoints ===")
    
    async with httpx.AsyncClient() as client:
        # First, create a test customer
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
        
        print("Creating test customer...")
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Customer created with ID: {customer_id}")
        
        # Test PUT endpoint (complete update)
        print("\nTesting PUT endpoint (complete update)...")
        put_data = {
            "email": f"updated.{uuid4().hex[:8]}@example.com",
            "firstName": "Jane",
            "lastName": "Smith",
            "phone": "+0987654321",
            "address": {
                "street": "456 Updated St",
                "city": "Updated City",
                "postalCode": "54321",
                "country": "Updated Country"
            }
        }
        
        response = await client.put(f"{BASE_URL}/customers/{customer_id}", json=put_data)
        assert response.status_code == 200, f"PUT request failed: {response.text}"
        updated_customer = response.json()
        assert updated_customer["email"] == put_data["email"]
        assert updated_customer["firstName"] == put_data["firstName"]
        assert updated_customer["lastName"] == put_data["lastName"]
        assert updated_customer["phone"] == put_data["phone"]
        print("✓ PUT endpoint works correctly")
        
        # Test PATCH endpoint (partial update)
        print("\nTesting PATCH endpoint (partial update)...")
        patch_data = {
            "firstName": "Janet",
            "phone": "+1111111111"
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data)
        assert response.status_code == 200, f"PATCH request failed: {response.text}"
        patched_customer = response.json()
        assert patched_customer["firstName"] == patch_data["firstName"]
        assert patched_customer["phone"] == patch_data["phone"]
        # Other fields should remain unchanged
        assert patched_customer["email"] == updated_customer["email"]
        assert patched_customer["lastName"] == updated_customer["lastName"]
        print("✓ PATCH endpoint works correctly")
        
        # Test PATCH with empty data (should return unchanged)
        print("\nTesting PATCH with empty data...")
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json={})
        assert response.status_code == 200, f"Empty PATCH request failed: {response.text}"
        unchanged_customer = response.json()
        assert unchanged_customer["firstName"] == patched_customer["firstName"]
        print("✓ PATCH with empty data works correctly")
        
        print("\n=== Customer Update Endpoints Test Completed Successfully ===\n")


async def test_claim_update_endpoints():
    """Test claim PUT and PATCH endpoints."""
    print("=== Testing Claim Update Endpoints ===")
    
    async with httpx.AsyncClient() as client:
        # First, create a test customer
        customer_data = {
            "email": f"claim.test.{uuid4().hex[:8]}@example.com",
            "firstName": "Claim",
            "lastName": "Tester",
            "phone": "+1234567890"
        }
        
        print("Creating test customer for claim...")
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        assert response.status_code == 201, f"Failed to create customer: {response.text}"
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Customer created with ID: {customer_id}")
        
        # Create a test claim
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
        
        print("Creating test claim...")
        response = await client.post(f"{BASE_URL}/claims/", json=claim_data)
        assert response.status_code == 201, f"Failed to create claim: {response.text}"
        created_claim = response.json()
        claim_id = created_claim["id"]
        print(f"✓ Claim created with ID: {claim_id}")
        
        # Test PUT endpoint (complete update)
        print("\nTesting PUT endpoint (complete update)...")
        put_data = {
            "customerId": customer_id,
            "flightInfo": {
                "flightNumber": "BA456",
                "airline": "British Airways",
                "departureDate": str(date.today()),
                "departureAirport": "LHR",
                "arrivalAirport": "CDG"
            },
            "incidentType": "cancellation",
            "notes": "Flight was cancelled"
        }
        
        response = await client.put(f"{BASE_URL}/claims/{claim_id}", json=put_data)
        assert response.status_code == 200, f"PUT request failed: {response.text}"
        updated_claim = response.json()
        assert updated_claim["flightNumber"] == put_data["flightInfo"]["flightNumber"]
        assert updated_claim["airline"] == put_data["flightInfo"]["airline"]
        assert updated_claim["incidentType"] == put_data["incidentType"]
        assert updated_claim["notes"] == put_data["notes"]
        print("✓ PUT endpoint works correctly")
        
        # Test PATCH endpoint (partial update)
        print("\nTesting PATCH endpoint (partial update)...")
        patch_data = {
            "incidentType": "denied_boarding",
            "notes": "Passenger was denied boarding"
        }
        
        response = await client.patch(f"{BASE_URL}/claims/{claim_id}", json=patch_data)
        assert response.status_code == 200, f"PATCH request failed: {response.text}"
        patched_claim = response.json()
        assert patched_claim["incidentType"] == patch_data["incidentType"]
        assert patched_claim["notes"] == patch_data["notes"]
        # Other fields should remain unchanged
        assert patched_claim["flightNumber"] == updated_claim["flightNumber"]
        assert patched_claim["airline"] == updated_claim["airline"]
        print("✓ PATCH endpoint works correctly")
        
        # Test PATCH with flight info update
        print("\nTesting PATCH with flight info update...")
        flight_patch_data = {
            "flightInfo": {
                "flightNumber": "AF789",
                "airline": "Air France",
                "departureDate": str(date.today()),
                "departureAirport": "CDG",
                "arrivalAirport": "FCO"
            }
        }
        
        response = await client.patch(f"{BASE_URL}/claims/{claim_id}", json=flight_patch_data)
        assert response.status_code == 200, f"Flight info PATCH failed: {response.text}"
        flight_patched_claim = response.json()
        assert flight_patched_claim["flightNumber"] == flight_patch_data["flightInfo"]["flightNumber"]
        assert flight_patched_claim["airline"] == flight_patch_data["flightInfo"]["airline"]
        # Other fields should remain unchanged
        assert flight_patched_claim["incidentType"] == patched_claim["incidentType"]
        print("✓ PATCH with flight info works correctly")
        
        print("\n=== Claim Update Endpoints Test Completed Successfully ===\n")


async def test_error_cases():
    """Test error cases for PUT and PATCH endpoints."""
    print("=== Testing Error Cases ===")
    
    async with httpx.AsyncClient() as client:
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        
        # Test PUT with non-existent customer
        print("Testing PUT with non-existent customer...")
        put_data = {
            "email": "test@example.com",
            "firstName": "Test",
            "lastName": "User",
            "phone": "+1234567890"
        }
        response = await client.put(f"{BASE_URL}/customers/{non_existent_id}", json=put_data)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PUT with non-existent customer returns 404")
        
        # Test PATCH with non-existent customer
        print("Testing PATCH with non-existent customer...")
        patch_data = {"firstName": "Updated"}
        response = await client.patch(f"{BASE_URL}/customers/{non_existent_id}", json=patch_data)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PATCH with non-existent customer returns 404")
        
        # Test PUT with non-existent claim
        print("Testing PUT with non-existent claim...")
        claim_put_data = {
            "customerId": non_existent_id,
            "flightInfo": {
                "flightNumber": "TEST123",
                "airline": "Test Air",
                "departureDate": str(date.today()),
                "departureAirport": "TST",
                "arrivalAirport": "TST"
            },
            "incidentType": "delay",
            "notes": "Test claim"
        }
        response = await client.put(f"{BASE_URL}/claims/{non_existent_id}", json=claim_put_data)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PUT with non-existent claim returns 404")
        
        # Test PATCH with non-existent claim
        print("Testing PATCH with non-existent claim...")
        claim_patch_data = {"incidentType": "cancellation"}
        response = await client.patch(f"{BASE_URL}/claims/{non_existent_id}", json=claim_patch_data)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PATCH with non-existent claim returns 404")
        
        print("\n=== Error Cases Test Completed Successfully ===\n")


async def main():
    """Run all tests."""
    print("Starting PUT and PATCH endpoints tests...")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_customer_update_endpoints()
        await test_claim_update_endpoints()
        await test_error_cases()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")
        print("PUT and PATCH endpoints are working correctly.")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())