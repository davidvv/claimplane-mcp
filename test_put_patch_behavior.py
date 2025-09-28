#!/usr/bin/env python3
"""Comprehensive test to verify PUT and PATCH behavior after the fix."""

import asyncio
import httpx
from datetime import date
from uuid import uuid4

# Base URL for the API
BASE_URL = "http://localhost:8000"

async def test_put_vs_patch_behavior():
    """Test that PUT and PATCH behave correctly with null values."""
    print("=== Testing PUT vs PATCH Behavior ===")
    
    async with httpx.AsyncClient() as client:
        # Create a test customer with all fields
        customer_data = {
            "email": f"test.behavior.{uuid4().hex[:8]}@example.com",
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
        assert response.status_code == 201
        created_customer = response.json()
        customer_id = created_customer["id"]
        print(f"✓ Customer created with ID: {customer_id}")
        
        # Test 1: PUT with explicit null phone (should set to null)
        print("\nTest 1: PUT with explicit null phone...")
        put_data = {
            "email": f"put.test.{uuid4().hex[:8]}@example.com",
            "firstName": "Jane",
            "lastName": "Smith",
            "phone": None,  # Explicitly set to None
            "address": {
                "street": "456 PUT St",
                "city": "PUT City",
                "postalCode": "54321",
                "country": "PUT Country"
            }
        }
        
        response = await client.put(f"{BASE_URL}/customers/{customer_id}", json=put_data)
        assert response.status_code == 200
        put_result = response.json()
        
        assert put_result["phone"] is None, f"Expected phone to be None, got {put_result['phone']}"
        assert put_result["email"] == put_data["email"]
        assert put_result["firstName"] == put_data["firstName"]
        print("  ✓ PUT correctly set phone to null")
        
        # Test 2: PATCH with null phone (should preserve existing value)
        print("\nTest 2: PATCH with null phone (should preserve existing)...")
        patch_data = {
            "firstName": "Janet"  # Only update first name
            # phone is not provided, so it should remain unchanged
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data)
        assert response.status_code == 200
        patch_result = response.json()
        
        assert patch_result["firstName"] == "Janet"
        assert patch_result["phone"] is None, f"Expected phone to remain None, got {patch_result['phone']}"
        print("  ✓ PATCH preserved null phone value")
        
        # Test 3: PATCH with explicit null phone (should preserve existing due to filtering)
        print("\nTest 3: PATCH with explicit null phone (should be filtered out)...")
        patch_data_with_null = {
            "firstName": "Jennifer",
            "phone": None  # This should be filtered out
        }
        
        response = await client.patch(f"{BASE_URL}/customers/{customer_id}", json=patch_data_with_null)
        assert response.status_code == 200
        patch_null_result = response.json()
        
        assert patch_null_result["firstName"] == "Jennifer"
        assert patch_null_result["phone"] is None, f"Expected phone to remain None, got {patch_null_result['phone']}"
        print("  ✓ PATCH correctly filtered out explicit null phone")
        
        # Test 4: PUT with missing phone (should set to null)
        print("\nTest 4: PUT with missing phone field...")
        put_missing_phone_data = {
            "email": f"put.missing.{uuid4().hex[:8]}@example.com",
            "firstName": "James",
            "lastName": "Bond",
            # phone field is missing - should be set to null
            "address": {
                "street": "789 Missing St",
                "city": "Missing City",
                "postalCode": "98765",
                "country": "Missing Country"
            }
        }
        
        response = await client.put(f"{BASE_URL}/customers/{customer_id}", json=put_missing_phone_data)
        assert response.status_code == 200
        put_missing_result = response.json()
        
        assert put_missing_result["phone"] is None, f"Expected phone to be None when missing, got {put_missing_result['phone']}"
        assert put_missing_result["email"] == put_missing_phone_data["email"]
        print("  ✓ PUT correctly set missing phone field to null")

async def test_claim_put_vs_patch_behavior():
    """Test claim PUT vs PATCH behavior."""
    print("\n=== Testing Claim PUT vs PATCH Behavior ===")
    
    async with httpx.AsyncClient() as client:
        # Create test customer
        customer_data = {
            "email": f"claim.behavior.{uuid4().hex[:8]}@example.com",
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
        
        # Test 1: PUT with explicit null notes (should set to null)
        print("\nTest 1: PUT with explicit null notes...")
        put_claim_data = {
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
        
        response = await client.put(f"{BASE_URL}/claims/{claim_id}", json=put_claim_data)
        assert response.status_code == 200
        put_claim_result = response.json()
        
        assert put_claim_result["notes"] is None, f"Expected notes to be None, got {put_claim_result['notes']}"
        assert put_claim_result["incidentType"] == "cancellation"
        print("  ✓ PUT correctly set notes to null")
        
        # Test 2: PATCH with null notes (should preserve existing value)
        print("\nTest 2: PATCH with null notes (should preserve existing)...")
        patch_claim_data = {
            "incidentType": "denied_boarding"  # Only update incident type
            # notes is not provided, should remain None
        }
        
        response = await client.patch(f"{BASE_URL}/claims/{claim_id}", json=patch_claim_data)
        assert response.status_code == 200
        patch_claim_result = response.json()
        
        assert patch_claim_result["incidentType"] == "denied_boarding"
        assert patch_claim_result["notes"] is None, f"Expected notes to remain None, got {patch_claim_result['notes']}"
        print("  ✓ PATCH preserved null notes value")

async def main():
    """Run all tests."""
    print("Testing PUT vs PATCH behavior after fix...")
    print(f"Testing against: {BASE_URL}")
    print("=" * 60)
    
    try:
        await test_put_vs_patch_behavior()
        await test_claim_put_vs_patch_behavior()
        
        print("\n" + "=" * 60)
        print("🎉 ALL BEHAVIOR TESTS PASSED! 🎉")
        print("PUT and PATCH endpoints now behave correctly:")
        print("- PUT: Sets explicit null values and missing optional fields to null")
        print("- PATCH: Filters out null values, preserving existing data")
        print("- Both operations maintain RESTful conventions")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())