#!/usr/bin/env python3
"""
Comprehensive API Integration Test Script
Tests all endpoints used by the claim workflow UI
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date
from uuid import uuid4

API_BASE = "http://localhost:8000"
TEST_EMAIL = f"test_{uuid4().hex[:8]}@example.com"

class ClaimWorkflowTester:
    def __init__(self):
        self.session = None
        self.csrf_token = None
        self.results = []
        self.claim_id = None
        self.draft_claim_id = None
        self.access_token = None
        self.customer_id = None
        
    def log(self, test_name: str, success: bool, message: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        self.results.append((test_name, success, message))
        
    async def setup(self):
        self.session = aiohttp.ClientSession()
        
    async def teardown(self):
        if self.session:
            await self.session.close()
            
    async def make_request(self, method: str, endpoint: str, **kwargs) -> tuple:
        """Make API request and return (success, status_code, response)"""
        url = f"{API_BASE}{endpoint}"
        try:
            async with self.session.request(method, url, **kwargs) as resp:
                try:
                    data = await resp.json()
                except:
                    data = await resp.text()
                return resp.status, data
        except Exception as e:
            return None, str(e)
            
    async def test_health(self):
        """Test API health endpoint"""
        status, data = await self.make_request("GET", "/health")
        self.log("Health Check", status == 200, f"Status: {status}")
        
    async def test_eligibility_check(self):
        """Test eligibility check endpoint"""
        payload = {
            "flight_info": {
                "flight_number": "LH400",
                "airline": "Lufthansa",
                "departure_date": "2024-12-25",
                "departure_airport": "FRA",
                "arrival_airport": "JFK"
            },
            "customer_info": {"email": TEST_EMAIL}
        }
        status, data = await self.make_request("POST", "/eligibility/check", json=payload)
        success = status in [200, 201]
        self.log("Eligibility Check", success, f"Status: {status}, Eligible: {data.get('eligible') if isinstance(data, dict) else data}")
        return data.get('eligible', False) if isinstance(data, dict) else False
        
    async def test_create_draft_claim(self):
        """Test draft claim creation"""
        payload = {
            "email": TEST_EMAIL,
            "flight_info": {
                "flight_number": "LH400",
                "airline": "Lufthansa",
                "departure_date": "2024-12-25",
                "departure_airport": "FRA",
                "arrival_airport": "JFK"
            },
            "incident_type": "delay"
        }
        status, data = await self.make_request("POST", "/claims/draft", json=payload)
        success = status in [200, 201]
        if success and isinstance(data, dict):
            self.claim_id = data.get('claim', {}).get('id') if isinstance(data.get('claim'), dict) else data.get('claim', {}).get('id', data.get('claim_id'))
            self.access_token = data.get('accessToken') or data.get('access_token')
        self.log("Create Draft Claim", success, f"Status: {status}, Claim ID: {self.claim_id}")
        return success
        
    async def test_submit_claim(self, eligible: bool):
        """Test claim submission"""
        if not self.claim_id:
            payload = {
                "email": TEST_EMAIL,
                "flight_info": {
                    "flight_number": "LH400",
                    "airline": "Lufthansa",
                    "departure_date": "2024-12-25",
                    "departure_airport": "FRA",
                    "arrival_airport": "JFK"
                },
                "customer_info": {
                    "first_name": "Test",
                    "last_name": "User",
                    "phone": "+1234567890",
                    "street": "123 Test St",
                    "city": "Test City",
                    "postal_code": "12345",
                    "country": "Germany",
                    "region": "EU"
                },
                "incident_type": "delay",
                "booking_reference": "ABC123",
                "ticket_number": "1234567890123",
                "terms_accepted": True
            }
        else:
            payload = {
                "email": TEST_EMAIL,
                "customer_info": {
                    "first_name": "Test",
                    "last_name": "User",
                    "phone": "+1234567890",
                    "street": "123 Test St",
                    "city": "Test City",
                    "postal_code": "12345",
                    "country": "Germany",
                    "region": "EU"
                },
                "terms_accepted": True
            }
            
        status, data = await self.make_request("POST", "/claims/submit", json=payload)
        success = status in [200, 201]
        if success and isinstance(data, dict):
            claim_data = data.get('claim')
            if isinstance(claim_data, dict):
                self.claim_id = claim_data.get('id')
                self.access_token = data.get('accessToken') or data.get('access_token')
        self.log("Submit Claim", success, f"Status: {status}")
        return success
        
    async def test_get_claim(self):
        """Test get claim by ID"""
        if not self.claim_id:
            self.log("Get Claim", False, "No claim ID available")
            return False
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        status, data = await self.make_request("GET", f"/claims/{self.claim_id}", headers=headers)
        success = status == 200
        self.log("Get Claim", success, f"Status: {status}")
        return success
        
    async def test_upload_document(self):
        """Test document upload"""
        if not self.claim_id:
            self.log("Upload Document", False, "No claim ID available")
            return False
            
        # Create a test PDF file
        test_content = b"%PDF-1.4 test document content"
        
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        headers["Content-Type"] = "multipart/form-data"
        
        form_data = aiohttp.FormData()
        form_data.add_field('file',
                           test_content,
                           filename='test_boarding_pass.pdf',
                           content_type='application/pdf')
        form_data.add_field('document_type', 'boarding_pass')
        
        status, data = await self.make_request("POST", f"/claims/{self.claim_id}/documents", data=form_data, headers=headers)
        success = status in [200, 201, 202]
        self.log("Upload Document", success, f"Status: {status}")
        return success
        
    async def test_list_documents(self):
        """Test list documents endpoint"""
        if not self.claim_id:
            self.log("List Documents", False, "No claim ID available")
            return False
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        status, data = await self.make_request("GET", f"/claims/{self.claim_id}/documents", headers=headers)
        success = status == 200
        self.log("List Documents", success, f"Status: {status}, Count: {len(data) if isinstance(data, list) else 'N/A'}")
        return success
        
    async def test_auth_magic_link(self):
        """Test magic link flow"""
        status, data = await self.make_request("POST", "/auth/magic-link/send", json={"email": TEST_EMAIL})
        self.log("Send Magic Link", status in [200, 201, 202], f"Status: {status}")
        
    async def test_customer_profile(self):
        """Test customer profile endpoints"""
        # Get current customer
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        status, data = await self.make_request("GET", "/customers/me", headers=headers)
        success = status == 200
        if success and isinstance(data, dict):
            self.customer_id = data.get('id')
        self.log("Get Customer Profile", success, f"Status: {status}")
        
        # Update customer
        if self.customer_id:
            update_payload = {
                "first_name": "Updated",
                "last_name": "User",
                "phone": "+1987654321"
            }
            status, data = await self.make_request("PUT", "/customers/me", json=update_payload, headers=headers)
            self.log("Update Customer Profile", status == 200, f"Status: {status}")
        
    async def test_list_claims(self):
        """Test list claims endpoint"""
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        status, data = await self.make_request("GET", "/claims/", headers=headers)
        success = status == 200
        count = len(data) if isinstance(data, list) else 0
        self.log("List Claims", success, f"Status: {status}, Count: {count}")
        return success
        
    async def run_all_tests(self):
        """Run all tests in workflow order"""
        print("=" * 60)
        print("CLAIM WORKFLOW API INTEGRATION TEST")
        print("=" * 60)
        print(f"Test started at: {datetime.now()}")
        print(f"Test email: {TEST_EMAIL}")
        print("=" * 60)
        
        await self.setup()
        
        try:
            # Basic tests
            await self.test_health()
            
            # Auth tests
            await self.test_auth_magic_link()
            
            # Core workflow tests
            eligible = await self.test_eligibility_check()
            await self.test_create_draft_claim()
            await self.test_submit_claim(eligible)
            await self.test_get_claim()
            await self.test_upload_document()
            await self.test_list_documents()
            await self.test_customer_profile()
            await self.test_list_claims()
            
        finally:
            await self.teardown()
            
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        passed = sum(1 for _, success, _ in self.results if success)
        failed = len(self.results) - passed
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print("=" * 60)
        
        if failed > 0:
            print("\nFailed Tests:")
            for test_name, success, message in self.results:
                if not success:
                    print(f"  - {test_name}: {message}")
        
        return failed == 0

if __name__ == "__main__":
    tester = ClaimWorkflowTester()
    success = asyncio.run(tester.run_all_tests())
    exit(0 if success else 1)
