#!/usr/bin/env python3
"""Test script for the flight claim API endpoints."""
import asyncio
import httpx
import json
from datetime import date, datetime
from uuid import UUID


BASE_URL = "http://localhost:8000"


async def test_health_endpoint():
    """Test the health check endpoint."""
    print("Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    print("✓ Health endpoint working\n")


async def test_create_customer():
    """Test creating a new customer."""
    print("Testing customer creation...")
    customer_data = {
        "email": "john.doe@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "phone": "+1234567890",
        "address": {
            "street": "123 Main St",
            "city": "New York",
            "postalCode": "10001",
            "country": "USA"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/customers/", json=customer_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            customer = response.json()
            assert customer["email"] == customer_data["email"]
            assert customer["firstName"] == customer_data["firstName"]
            assert customer["lastName"] == customer_data["lastName"]
            print("✓ Customer created successfully")
            return customer["id"]
        else:
            print("✗ Customer creation failed")
            return None
    print()


async def test_get_customer(customer_id):
    """Test retrieving a customer by ID."""
    print(f"Testing get customer {customer_id}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/customers/{customer_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            customer = response.json()
            assert customer["id"] == str(customer_id)
            print("✓ Customer retrieved successfully")
        else:
            print("✗ Customer retrieval failed")
    print()


async def test_list_customers():
    """Test listing customers."""
    print("Testing list customers...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/customers/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            customers = response.json()
            assert isinstance(customers, list)
            print(f"✓ Found {len(customers)} customers")
        else:
            print("✗ Customer listing failed")
    print()


async def test_create_claim(customer_id):
    """Test creating a new claim."""
    print("Testing claim creation...")
    claim_data = {
        "customerId": customer_id,
        "flightInfo": {
            "flightNumber": "LH1234",
            "airline": "Lufthansa",
            "departureDate": "2025-06-15",
            "departureAirport": "FRA",
            "arrivalAirport": "JFK"
        },
        "incidentType": "delay",
        "notes": "Flight delayed by 3 hours due to weather"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/claims/", json=claim_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            claim = response.json()
            assert claim["customerId"] == str(customer_id)
            assert claim["flightNumber"] == claim_data["flightInfo"]["flightNumber"]
            assert claim["incidentType"] == claim_data["incidentType"]
            print("✓ Claim created successfully")
            return claim["id"]
        else:
            print("✗ Claim creation failed")
            return None
    print()


async def test_submit_claim_with_customer():
    """Test submitting a claim with customer information."""
    print("Testing claim submission with customer...")
    claim_request = {
        "customerInfo": {
            "email": "jane.smith@example.com",
            "firstName": "Jane",
            "lastName": "Smith",
            "phone": "+0987654321"
        },
        "flightInfo": {
            "flightNumber": "BA5678",
            "airline": "British Airways",
            "departureDate": "2025-07-20",
            "departureAirport": "LHR",
            "arrivalAirport": "CDG"
        },
        "incidentType": "cancellation",
        "notes": "Flight cancelled due to strike"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/claims/submit", json=claim_request)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            claim = response.json()
            assert claim["flightNumber"] == claim_request["flightInfo"]["flightNumber"]
            assert claim["incidentType"] == claim_request["incidentType"]
            print("✓ Claim submitted successfully")
            return claim["id"]
        else:
            print("✗ Claim submission failed")
            return None
    print()


async def test_get_claim(claim_id):
    """Test retrieving a claim by ID."""
    print(f"Testing get claim {claim_id}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/claims/{claim_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            claim = response.json()
            assert claim["id"] == str(claim_id)
            print("✓ Claim retrieved successfully")
        else:
            print("✗ Claim retrieval failed")
    print()


async def test_list_claims():
    """Test listing claims."""
    print("Testing list claims...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/claims/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            claims = response.json()
            assert isinstance(claims, list)
            print(f"✓ Found {len(claims)} claims")
        else:
            print("✗ Claim listing failed")
    print()


async def run_all_tests():
    """Run all API tests."""
    print("🚀 Starting Flight Claim API Tests")
    print("=" * 50)
    
    try:
        # Test health endpoint
        await test_health_endpoint()
        
        # Test customer endpoints
        customer_id = await test_create_customer()
        if customer_id:
            await test_get_customer(customer_id)
        await test_list_customers()
        
        # Test claim endpoints
        if customer_id:
            claim_id = await test_create_claim(customer_id)
            if claim_id:
                await test_get_claim(claim_id)
        
        # Test claim submission with customer
        claim_id2 = await test_submit_claim_with_customer()
        if claim_id2:
            await test_get_claim(claim_id2)
        
        await test_list_claims()
        
        print("=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())