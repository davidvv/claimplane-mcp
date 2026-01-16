"""User and admin management tools."""
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from database import get_db_session
from app.models import Customer
from app.repositories import CustomerRepository
# from app.services.password_service import PasswordService


async def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "customer"
) -> Dict[str, Any]:
    """Create a new user.
    
    Args:
        email: User email address
        password: User password
        first_name: First name
        last_name: Last name
        role: User role (customer, admin, support)
    
    Returns:
        Created user details
    """
    try:
        async with get_db_session() as session:
            customer_repo = CustomerRepository(session)
            
            # Hash password
            # password_hash = PasswordService.hash_password(password)
            # TODO: Implement proper hashing when passlib is available
            password_hash = f"noop:{password}"
            
            # Create customer/user
            customer = await customer_repo.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=password_hash,
                role=role,
                is_active=True,
                is_email_verified=False
            )
            
            return {
                "success": True,
                "user_id": str(customer.id),
                "email": customer.email,
                "role": customer.role,
                "name": f"{customer.first_name} {customer.last_name}",
                "message": f"User created successfully: {email}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create user"
        }


async def create_admin(
    email: str,
    password: str,
    first_name: str,
    last_name: str
) -> Dict[str, Any]:
    """Create a new admin user.
    
    Args:
        email: Admin email address
        password: Admin password
        first_name: First name
        last_name: Last name
    
    Returns:
        Created admin details
    """
    return await create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role="admin"
    )


async def get_user(user_id: str) -> Dict[str, Any]:
    """Get user by ID.
    
    Args:
        user_id: User ID (UUID)
    
    Returns:
        User details
    """
    try:
        async with get_db_session() as session:
            customer_repo = CustomerRepository(session)
            customer = await customer_repo.get_by_id(user_id)
            
            if not customer:
                return {
                    "success": False,
                    "message": f"User not found: {user_id}"
                }
            
            return {
                "success": True,
                "user": {
                    "id": str(customer.id),
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "role": customer.role,
                    "is_email_verified": customer.is_email_verified,
                    "is_active": customer.is_active,
                    "created_at": customer.created_at.isoformat() if customer.created_at else None,
                    "last_login_at": customer.last_login_at.isoformat() if customer.last_login_at else None
                },
                "message": "User retrieved successfully"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve user"
        }


async def get_user_by_email(email: str) -> Dict[str, Any]:
    """Get user by email address.
    
    Args:
        email: User email
    
    Returns:
        User details or not found
    """
    try:
        async with get_db_session() as session:
            customer_repo = CustomerRepository(session)
            customer = await customer_repo.get_by_email(email)
            
            if not customer:
                return {
                    "success": False,
                    "found": False,
                    "message": f"No user found with email: {email}"
                }
            
            return {
                "success": True,
                "found": True,
                "user": {
                    "id": str(customer.id),
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "role": customer.role,
                    "is_email_verified": customer.is_email_verified,
                    "is_active": customer.is_active,
                    "created_at": customer.created_at.isoformat() if customer.created_at else None
                },
                "message": f"User found: {customer.first_name} {customer.last_name}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to search for user"
        }


async def list_users(
    role: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    """List users with optional role filter.
    
    Args:
        role: Filter by role (customer, admin, support)
        limit: Number of results (default: 10)
        offset: Number to skip (default: 0)
    
    Returns:
        List of users
    """
    try:
        async with get_db_session() as session:
            query = select(Customer).order_by(Customer.created_at.desc())
            
            if role:
                query = query.where(Customer.role == role)
            
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            users = result.scalars().all()
            
            return {
                "success": True,
                "count": len(users),
                "role_filter": role,
                "users": [
                    {
                        "id": str(u.id),
                        "email": u.email,
                        "name": f"{u.first_name} {u.last_name}",
                        "role": u.role,
                        "is_active": u.is_active,
                        "created_at": u.created_at.isoformat() if u.created_at else None
                    }
                    for u in users
                ],
                "message": f"Retrieved {len(users)} users"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list users"
        }


async def update_user(
    user_id: str,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_email_verified: Optional[bool] = None
) -> Dict[str, Any]:
    """Update user details.
    
    Args:
        user_id: User ID (UUID)
        email: New email (optional)
        first_name: New first name (optional)
        last_name: New last name (optional)
        role: New role (optional)
        is_active: Active status (optional)
        is_email_verified: Email verified status (optional)
    
    Returns:
        Updated user details
    """
    try:
        async with get_db_session() as session:
            customer_repo = CustomerRepository(session)
            customer = await customer_repo.get_by_id(user_id)
            
            if not customer:
                return {
                    "success": False,
                    "message": f"User not found: {user_id}"
                }
            
            # Update fields if provided
            if email is not None:
                customer.email = email
            if first_name is not None:
                customer.first_name = first_name
            if last_name is not None:
                customer.last_name = last_name
            if role is not None:
                customer.role = role
            if is_active is not None:
                customer.is_active = is_active
            if is_email_verified is not None:
                customer.is_email_verified = is_email_verified
            
            await session.commit()
            
            return {
                "success": True,
                "user_id": str(customer.id),
                "email": customer.email,
                "name": f"{customer.first_name} {customer.last_name}",
                "role": customer.role,
                "is_active": customer.is_active,
                "message": "User updated successfully"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to update user"
        }


async def delete_user(user_id: str) -> Dict[str, Any]:
    """Delete a user.
    
    Args:
        user_id: User ID (UUID)
    
    Returns:
        Deletion status
    """
    try:
        async with get_db_session() as session:
            customer_repo = CustomerRepository(session)
            customer = await customer_repo.get_by_id(user_id)
            
            if not customer:
                return {
                    "success": False,
                    "message": f"User not found: {user_id}"
                }
            
            email = customer.email
            await customer_repo.delete(user_id)
            await session.commit()
            
            return {
                "success": True,
                "user_id": user_id,
                "email": email,
                "message": f"User deleted: {email}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to delete user"
        }


async def activate_user(user_id: str) -> Dict[str, Any]:
    """Activate a user account.
    
    Args:
        user_id: User ID (UUID)
    
    Returns:
        Activation status
    """
    return await update_user(user_id=user_id, is_active=True)


async def deactivate_user(user_id: str) -> Dict[str, Any]:
    """Deactivate a user account.
    
    Args:
        user_id: User ID (UUID)
    
    Returns:
        Deactivation status
    """
    return await update_user(user_id=user_id, is_active=False)


async def verify_user_email(user_id: str) -> Dict[str, Any]:
    """Mark user email as verified.
    
    Args:
        user_id: User ID (UUID)
    
    Returns:
        Verification status
    """
    return await update_user(user_id=user_id, is_email_verified=True)
