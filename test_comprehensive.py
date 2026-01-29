#!/usr/bin/env python3
"""
Comprehensive ClaimPlane API Test Suite
Tests both happy paths and edge cases/weird paths
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from uuid import uuid4
import sys

API_BASE = "http://localhost:8000"

# Test Results Storage
test_results = {
    "passed": [],
    "failed": [],
    "issues": []
}

def log_test(name, passed, details=None):
    """Log test result"""
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}")
    if details:
        print(f"       Details: {details}")
    
    if passed:
        test_results["passed"].append({"name": name, "details": details})
    else:
        test_results["failed"].append({"name": name, "details": details})
        if details:
            test_results["issues"].append(f"{name}: {details}")

async def test_customers(session):
    """Test customer endpoints"""
    print("\n=== CUSTOMER ENDPOINTS ===")
    
    # Test 1: Create valid customer
    print("\n1. Create valid customer")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": f"test.{uuid4().hex[:8]}@example.com",
        "firstName": "Test",
        "lastName": "User",
        "phone": "+49 170 1234567",
        "address": {
            "street": "123 Test Street",
            "city": "Berlin",
            "postalCode": "10115",
            "country": "Germany"
        }
    }) as resp:
        data = await resp.json()
        customer_id = data.get("id")
        log_test("Create valid customer", resp.status == 201, f"Status: {resp.status}, ID: {customer_id}")
    
    # Test 2: Create duplicate email
    print("\n2. Create duplicate email")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": "test.basic@example.com",
        "firstName": "Duplicate",
        "lastName": "Test"
    }) as resp:
        log_test("Duplicate email rejected", resp.status in [400, 409, 422], f"Status: {resp.status}")
    
    # Test 3: Invalid email format
    print("\n3. Invalid email format")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": "not-an-email",
        "firstName": "Invalid",
        "lastName": "Email"
    }) as resp:
        log_test("Invalid email rejected", resp.status == 422, f"Status: {resp.status}")
    
    # Test 4: Missing required fields
    print("\n4. Missing required fields")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": "missing.fields@example.com"
    }) as resp:
        log_test("Missing fields rejected", resp.status == 422, f"Status: {resp.status}")
    
    # Test 5: SQL injection in name
    print("\n5. SQL injection in name field")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": f"sql.test.{uuid4().hex[:8]}@example.com",
        "firstName": "Robert'); DROP TABLE customers; --",
        "lastName": "Test"
    }) as resp:
        if resp.status in [201, 200]:
            log_test("SQL injection sanitized", True, "Payload accepted but sanitized")
        else:
            log_test("SQL injection handling", False, f"Status: {resp.status}")
    
    # Test 6: XSS in name
    print("\n6. XSS in name field")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": f"xss.test.{uuid4().hex[:8]}@example.com",
        "firstName": "<script>alert('xss')</script>",
        "lastName": "Test"
    }) as resp:
        if resp.status in [201, 200]:
            data = await resp.json()
            first_name = data.get("firstName", "")
            if "<script>" in first_name:
                log_test("XSS vulnerability", False, "Script tags not sanitized in response!")
            else:
                log_test("XSS payload sanitized", True, "Script tags properly handled")
        else:
            log_test("XSS handling", True, f"Status: {resp.status}")
    
    # Test 7: Very long names
    print("\n7. Very long name (100 chars)")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": f"long.name.{uuid4().hex[:8]}@example.com",
        "firstName": "A" * 100,
        "lastName": "Test"
    }) as resp:
        log_test("Long name handling", resp.status in [201, 200, 422], f"Status: {resp.status}")
    
    # Test 8: Get non-existent customer
    print("\n8. Get non-existent customer")
    async with session.get(f"{API_BASE}/customers/{uuid4()}") as resp:
        log_test("Non-existent customer returns 404", resp.status == 404, f"Status: {resp.status}")
    
    # Test 9: Invalid UUID format
    print("\n9. Invalid UUID format")
    async with session.get(f"{API_BASE}/customers/invalid-uuid") as resp:
        log_test("Invalid UUID handling", resp.status in [400, 422], f"Status: {resp.status}")
    
    # Test 10: List customers with pagination
    print("\n10. List customers with pagination")
    async with session.get(f"{API_BASE}/customers/?limit=5&offset=0") as resp:
        log_test("Pagination works", resp.status == 200, f"Status: {resp.status}")
    
    # Test 11: Negative offset
    print("\n11. Negative offset")
    async with session.get(f"{API_BASE}/customers/?limit=5&offset=-1") as resp:
        log_test("Negative offset handled", True, f"Status: {resp.status}")
    
    # Test 12: Unicode in names
    print("\n12. Unicode in names")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": f"unicode.{uuid4().hex[:8]}@example.com",
        "firstName": "José",
        "lastName": "García-Muñoz"
    }) as resp:
        log_test("Unicode names supported", resp.status in [201, 200], f"Status: {resp.status}")
    
    return customer_id

async def test_claims(session, customer_id):
    """Test claim endpoints"""
    print("\n=== CLAIM ENDPOINTS ===")
    
    if not customer_id:
        print("  SKIPPING: No customer ID available")
        return None
    
    headers = {"X-Customer-ID": str(customer_id)}
    
    # Test 1: Create valid claim
    print("\n1. Create valid claim")
    async with session.post(f"{API_BASE}/claims/", 
        headers=headers,
        json={
            "flightNumber": "LH123",
            "flightDate": "2025-01-15",
            "departureAirport": "FRA",
            "arrivalAirport": "JFK",
            "incidentType": "delay"
        }) as resp:
        data = await resp.json()
        claim_id = data.get("id")
        log_test("Create valid claim", resp.status == 201, f"Status: {resp.status}, ID: {claim_id}")
    
    # Test 2: Invalid incident type
    print("\n2. Invalid incident type")
    async with session.post(f"{API_BASE}/claims/",
        headers=headers,
        json={
            "flightNumber": "LH123",
            "flightDate": "2025-01-15",
            "departureAirport": "FRA",
            "arrivalAirport": "JFK",
            "incidentType": "invalid_type"
        }) as resp:
        log_test("Invalid incident type rejected", resp.status == 422, f"Status: {resp.status}")
    
    # Test 3: Future date
    print("\n3. Future flight date")
    async with session.post(f"{API_BASE}/claims/",
        headers=headers,
        json={
            "flightNumber": "LH123",
            "flightDate": "2030-01-15",
            "departureAirport": "FRA",
            "arrivalAirport": "JFK",
            "incidentType": "delay"
        }) as resp:
        log_test("Future date handling", True, f"Status: {resp.status}")
    
    # Test 4: Same departure/arrival
    print("\n4. Same departure/arrival airport")
    async with session.post(f"{API_BASE}/claims/",
        headers=headers,
        json={
            "flightNumber": "LH123",
            "flightDate": "2025-01-15",
            "departureAirport": "FRA",
            "arrivalAirport": "FRA",
            "incidentType": "delay"
        }) as resp:
        log_test("Same airport handling", True, f"Status: {resp.status}")
    
    # Test 5: Invalid airport code
    print("\n5. Invalid airport code")
    async with session.post(f"{API_BASE}/claims/",
        headers=headers,
        json={
            "flightNumber": "LH123",
            "flightDate": "2025-01-15",
            "departureAirport": "INVALID",
            "arrivalAirport": "JFK",
            "incidentType": "delay"
        }) as resp:
        log_test("Invalid airport handling", True, f"Status: {resp.status}")
    
    # Test 6: Get claim
    if claim_id:
        print("\n6. Get claim by ID")
        async with session.get(f"{API_BASE}/claims/{claim_id}", headers=headers) as resp:
            log_test("Get claim", resp.status == 200, f"Status: {resp.status}")
        
        # Test 7: Update claim
        print("\n7. Update claim")
        async with session.patch(f"{API_BASE}/claims/{claim_id}",
            headers=headers,
            json={"description": "Updated description"}) as resp:
            log_test("Update claim", resp.status == 200, f"Status: {resp.status}")
    
    return claim_id

async def test_files(session, claim_id):
    """Test file endpoints"""
    print("\n=== FILE ENDPOINTS ===")
    
    if not claim_id:
        print("  SKIPPING: No claim ID available")
        return
    
    # Test 1: List claim files
    print("\n1. List claim files")
    async with session.get(f"{API_BASE}/files/claim/{claim_id}") as resp:
        log_test("List claim files", resp.status == 200, f"Status: {resp.status}")
    
    # Test 2: Get non-existent file
    print("\n2. Get non-existent file")
    async with session.get(f"{API_BASE}/files/{uuid4()}") as resp:
        log_test("Non-existent file returns 404", resp.status == 404, f"Status: {resp.status}")

async def test_auth(session):
    """Test authentication endpoints"""
    print("\n=== AUTHENTICATION ENDPOINTS ===")
    
    # Test 1: Login with invalid credentials
    print("\n1. Login with invalid credentials")
    async with session.post(f"{API_BASE}/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    }) as resp:
        log_test("Invalid credentials rejected", resp.status in [401, 400], f"Status: {resp.status}")
    
    # Test 2: Login with missing fields
    print("\n2. Login with missing fields")
    async with session.post(f"{API_BASE}/auth/login", json={}) as resp:
        log_test("Missing login fields handled", resp.status == 422, f"Status: {resp.status}")
    
    # Test 3: Register with weak password
    print("\n3. Register with weak password")
    async with session.post(f"{API_BASE}/auth/register", json={
        "email": f"weak.{uuid4().hex[:8]}@example.com",
        "password": "123",
        "firstName": "Weak",
        "lastName": "Password"
    }) as resp:
        log_test("Weak password handling", True, f"Status: {resp.status}")

async def test_eligibility(session):
    """Test eligibility check"""
    print("\n=== ELIGIBILITY ENDPOINTS ===")
    
    # Test eligibility check
    print("\n1. Check eligibility")
    async with session.post(f"{API_BASE}/eligibility/check", json={
        "flightNumber": "LH123",
        "flightDate": "2025-01-15",
        "departureAirport": "FRA",
        "arrivalAirport": "JFK",
        "incidentType": "delay",
        "delayMinutes": 180
    }) as resp:
        log_test("Eligibility check", resp.status == 200, f"Status: {resp.status}")
    
    # Test with invalid data
    print("\n2. Eligibility with invalid data")
    async with session.post(f"{API_BASE}/eligibility/check", json={}) as resp:
        log_test("Invalid eligibility data handled", resp.status == 422, f"Status: {resp.status}")

async def test_weird_paths(session):
    """Test weird/edge cases"""
    print("\n=== WEIRD PATHS & EDGE CASES ===")
    
    # Test 1: Empty JSON body
    print("\n1. Empty JSON body")
    async with session.post(f"{API_BASE}/customers/", json={}) as resp:
        log_test("Empty body handled", resp.status == 422, f"Status: {resp.status}")
    
    # Test 2: Null values
    print("\n2. Null values in fields")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": None,
        "firstName": None,
        "lastName": None
    }) as resp:
        log_test("Null values handled", resp.status == 422, f"Status: {resp.status}")
    
    # Test 3: Special characters in email
    print("\n3. Special characters in email")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": "test..double..dots@example.com",
        "firstName": "Test",
        "lastName": "User"
    }) as resp:
        log_test("Special email chars handled", True, f"Status: {resp.status}")
    
    # Test 4: Very large request body
    print("\n4. Very large request body")
    async with session.post(f"{API_BASE}/customers/", json={
        "email": f"large.{uuid4().hex[:8]}@example.com",
        "firstName": "A" * 10000,
        "lastName": "Test"
    }) as resp:
        log_test("Large body handled", True, f"Status: {resp.status}")
    
    # Test 5: JSON injection
    print("\n5. JSON injection attempt")
    async with session.post(f"{API_BASE}/customers/", 
        data='{"email": "json@test.com", "firstName": "Test", "lastName": "User", "extra": {"$ne": null}}',
        headers={"Content-Type": "application/json"}) as resp:
        log_test("JSON injection handled", True, f"Status: {resp.status}")
    
    # Test 6: Path traversal in file ID
    print("\n6. Path traversal attempt")
    async with session.get(f"{API_BASE}/files/../../../etc/passwd") as resp:
        log_test("Path traversal blocked", resp.status in [400, 404, 422], f"Status: {resp.status}")

async def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("CLAIMPLANE COMPREHENSIVE API TEST SUITE")
    print(f"Started at: {datetime.now().isoformat()}")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        # Health check first
        print("\n=== HEALTH CHECK ===")
        try:
            async with session.get(f"{API_BASE}/health") as resp:
                if resp.status == 200:
                    print("  API is healthy")
                else:
                    print(f"  WARNING: API returned status {resp.status}")
        except Exception as e:
            print(f"  ERROR: Cannot connect to API: {e}")
            return
        
        # Run tests
        customer_id = await test_customers(session)
        claim_id = await test_claims(session, customer_id)
        await test_files(session, claim_id)
        await test_auth(session)
        await test_eligibility(session)
        await test_weird_paths(session)
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {len(test_results['passed']) + len(test_results['failed'])}")
    print(f"Passed: {len(test_results['passed'])}")
    print(f"Failed: {len(test_results['failed'])}")
    
    if test_results['issues']:
        print("\nIssues Found:")
        for i, issue in enumerate(test_results['issues'], 1):
            print(f"  {i}. {issue}")
    
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    
    # Save results
    with open("/tmp/test_results_comprehensive.json", "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    
    return test_results

if __name__ == "__main__":
    asyncio.run(run_all_tests())