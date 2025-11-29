"""Tests for customers endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Customer


@pytest.mark.asyncio
class TestCustomersSelfServiceEndpoints:
    """Test customer self-service endpoints (/me routes)."""

    async def test_get_my_profile(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test getting current user's profile."""
        response = await client.get("/customers/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_customer.email
        assert data["firstName"] == test_customer.first_name
        assert data["lastName"] == test_customer.last_name

    async def test_get_my_profile_unauthorized(self, client: AsyncClient):
        """Test getting profile without authentication."""
        response = await client.get("/customers/me")

        # May return 401 (Unauthorized) or 403 (Forbidden) depending on implementation
        assert response.status_code in [401, 403]

    async def test_update_my_profile_put(self, client: AsyncClient, auth_headers: dict):
        """Test updating own profile with PUT."""
        update_data = {
            "email": "updated@example.com",
            "firstName": "Updated",
            "lastName": "Name",
            "phone": "+9876543210",
            "address": {
                "street": "456 Updated St",
                "city": "Updated City",
                "postalCode": "54321",
                "country": "Updated Country"
            }
        }

        response = await client.put("/customers/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == update_data["email"]
        assert data["firstName"] == update_data["firstName"]

    async def test_update_my_profile_patch(self, client: AsyncClient, auth_headers: dict, test_customer: Customer):
        """Test partially updating own profile with PATCH."""
        patch_data = {
            "phone": "+1111111111"
        }

        response = await client.patch("/customers/me", json=patch_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == patch_data["phone"]
        # Email should remain unchanged
        assert data["email"] == test_customer.email


@pytest.mark.asyncio
class TestCustomersAdminEndpoints:
    """Test customer admin endpoints."""

    async def test_create_customer_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test creating a customer as admin."""
        customer_data = {
            "email": "admincreated@example.com",
            "firstName": "Admin",
            "lastName": "Created",
            "phone": "+1234567890",
            "address": {
                "street": "123 Admin St",
                "city": "Admin City",
                "postalCode": "12345",
                "country": "USA"
            }
        }

        response = await client.post("/customers/", json=customer_data, headers=admin_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == customer_data["email"]
        assert data["firstName"] == customer_data["firstName"]

    async def test_create_customer_as_regular_user(self, client: AsyncClient, auth_headers: dict):
        """Test creating a customer as regular user (should fail)."""
        customer_data = {
            "email": "usercreated@example.com",
            "firstName": "User",
            "lastName": "Created",
            "phone": "+1234567890"
        }

        response = await client.post("/customers/", json=customer_data, headers=auth_headers)

        assert response.status_code == 403

    async def test_create_customer_duplicate_email(self, client: AsyncClient, admin_headers: dict, test_customer: Customer):
        """Test creating customer with duplicate email."""
        customer_data = {
            "email": test_customer.email,
            "firstName": "Duplicate",
            "lastName": "Email",
            "phone": "+1234567890"
        }

        response = await client.post("/customers/", json=customer_data, headers=admin_headers)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_get_customer_by_id_as_admin(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_customer: Customer
    ):
        """Test getting customer by ID as admin."""
        response = await client.get(f"/customers/{test_customer.id}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_customer.id)
        assert data["email"] == test_customer.email

    async def test_get_customer_by_id_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_admin: Customer
    ):
        """Test getting customer by ID as regular user (should fail)."""
        response = await client.get(f"/customers/{test_admin.id}", headers=auth_headers)

        assert response.status_code == 403

    async def test_list_customers_as_admin(self, client: AsyncClient, admin_headers: dict):
        """Test listing all customers as admin."""
        response = await client.get("/customers/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_customers_as_regular_user(self, client: AsyncClient, auth_headers: dict):
        """Test listing customers as regular user (should fail)."""
        response = await client.get("/customers/", headers=auth_headers)

        assert response.status_code == 403

    async def test_list_customers_with_pagination(self, client: AsyncClient, admin_headers: dict):
        """Test listing customers with pagination."""
        response = await client.get("/customers/?skip=0&limit=10", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_search_customers_by_email(self, client: AsyncClient, admin_headers: dict, test_customer: Customer):
        """Test searching customers by email."""
        search_term = test_customer.email.split("@")[0]  # Use part of email
        response = await client.get(f"/customers/search/by-email/{search_term}", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_search_customers_by_name(self, client: AsyncClient, admin_headers: dict):
        """Test searching customers by name."""
        response = await client.get("/customers/search/by-name/Test", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_update_customer_as_admin_put(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_customer: Customer
    ):
        """Test updating customer as admin with PUT."""
        update_data = {
            "email": "adminupdated@example.com",
            "firstName": "AdminUpdated",
            "lastName": "Customer",
            "phone": "+9999999999",
            "address": {
                "street": "999 Admin St",
                "city": "Admin City",
                "postalCode": "99999",
                "country": "USA"
            }
        }

        response = await client.put(
            f"/customers/{test_customer.id}",
            json=update_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == update_data["email"]

    async def test_update_customer_as_admin_patch(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_customer: Customer
    ):
        """Test partially updating customer as admin with PATCH."""
        patch_data = {
            "phone": "+8888888888"
        }

        response = await client.patch(
            f"/customers/{test_customer.id}",
            json=patch_data,
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == patch_data["phone"]
        # Email should remain unchanged
        assert data["email"] == test_customer.email

    async def test_update_customer_not_found(self, client: AsyncClient, admin_headers: dict):
        """Test updating non-existent customer."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {
            "email": "notfound@example.com",
            "firstName": "Not",
            "lastName": "Found",
            "phone": "+1234567890"
        }

        response = await client.put(
            f"/customers/{fake_id}",
            json=update_data,
            headers=admin_headers
        )

        assert response.status_code == 404
