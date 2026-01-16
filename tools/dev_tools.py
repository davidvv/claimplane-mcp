"""Development utilities for testing and database management."""
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
import random
import uuid
from database import get_db_session
from app.models import Customer, Claim
from app.repositories import CustomerRepository, ClaimRepository


async def seed_realistic_data(scenario: str = "basic", count: int = 5) -> Dict[str, Any]:
    """Populate database with realistic test data.
    
    Args:
        scenario: Type of scenario (basic, complex, mixed)
        count: Number of test entities to create
    
    Returns:
        Summary of created entities
    """
    try:
        async with get_db_session() as session:
            customers_created = []
            claims_created = []
            
            customer_repo = CustomerRepository(session)
            claim_repo = ClaimRepository(session)
            
            # Sample data
            first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emma", "Robert", "Lisa"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
            cities = ["Berlin", "London", "Paris", "Madrid", "Rome", "Amsterdam", "Brussels", "Vienna"]
            countries = ["Germany", "UK", "France", "Spain", "Italy", "Netherlands", "Belgium", "Austria"]
            
            airports = ["FRA", "MUC", "LHR", "CDG", "MAD", "FCO", "AMS", "BRU"]
            airlines = ["LH", "BA", "AF", "IB", "AZ", "KL", "SN"]
            incident_types = ["delay", "cancellation", "denied_boarding", "missed_connection"]
            statuses = ["submitted", "under_review", "approved", "rejected", "paid"]
            
            for i in range(count):
                # Create customer
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                email = f"{first_name.lower()}.{last_name.lower()}{i}@test.com"
                city = random.choice(cities)
                country = random.choice(countries)
                
                customer = await customer_repo.create(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    phone=f"+49{random.randint(1000000000, 9999999999)}",
                    street=f"Test Street {random.randint(1, 100)}",
                    city=city,
                    postal_code=f"{random.randint(10000, 99999)}",
                    country=country
                )
                customers_created.append(str(customer.id))
                
                # Create 1-3 claims per customer
                num_claims = random.randint(1, 3 if scenario == "complex" else 1)
                
                for j in range(num_claims):
                    departure = random.choice(airports)
                    arrival = random.choice([a for a in airports if a != departure])
                    airline = random.choice(airlines)
                    flight_num = f"{airline}{random.randint(100, 999)}"
                    
                    flight_date = date.today() - timedelta(days=random.randint(1, 90))
                    delay = random.randint(60, 480)  # 1-8 hours
                    incident = random.choice(incident_types)
                    status = random.choice(statuses) if scenario == "mixed" else "submitted"
                    
                    # Calculate compensation based on distance
                    distance_map = {
                        ("FRA", "LHR"): 650,
                        ("LHR", "CDG"): 350,
                        ("MAD", "FCO"): 1400,
                    }
                    distance = distance_map.get((departure, arrival), 1000)
                    
                    if delay >= 180:
                        if distance <= 1500:
                            compensation = 250.0
                        elif distance <= 3500:
                            compensation = 400.0
                        else:
                            compensation = 600.0
                    else:
                        compensation = None
                    
                    claim = await claim_repo.create(
                        customer_id=customer.id,
                        flight_number=flight_num,
                        flight_date=flight_date,
                        departure_airport=departure,
                        arrival_airport=arrival,
                        incident_type=incident,
                        delay_minutes=delay,
                        compensation_amount=compensation,
                        status=status,
                        description=f"Test {incident} on flight {flight_num}"
                    )
                    claims_created.append(str(claim.id))
            
            return {
                "success": True,
                "scenario": scenario,
                "created": {
                    "customers": len(customers_created),
                    "claims": len(claims_created)
                },
                "customer_ids": customers_created,
                "claim_ids": claims_created,
                "message": f"Created {len(customers_created)} customers and {len(claims_created)} claims"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to seed test data"
        }


async def create_test_scenario(
    email: str = "test@example.com",
    scenario_type: str = "delayed_flight"
) -> Dict[str, Any]:
    """Create a complete test scenario (customer + claim).
    
    Args:
        email: Customer email
        scenario_type: Type (delayed_flight, cancelled_flight, denied_boarding)
    
    Returns:
        Created entities
    """
    try:
        async with get_db_session() as session:
            customer_repo = CustomerRepository(session)
            claim_repo = ClaimRepository(session)
            
            # Create customer
            customer = await customer_repo.create(
                email=email,
                first_name="Test",
                last_name="User",
                phone="+491234567890",
                street="Test Street 123",
                city="Berlin",
                postal_code="10115",
                country="Germany"
            )
            
            # Create claim based on scenario
            scenarios = {
                "delayed_flight": {
                    "flight_number": "LH456",
                    "departure": "FRA",
                    "arrival": "LHR",
                    "incident_type": "delay",
                    "delay_minutes": 240,
                    "compensation": 250.0
                },
                "cancelled_flight": {
                    "flight_number": "BA789",
                    "departure": "LHR",
                    "arrival": "CDG",
                    "incident_type": "cancellation",
                    "delay_minutes": None,
                    "compensation": 250.0
                },
                "denied_boarding": {
                    "flight_number": "AF123",
                    "departure": "CDG",
                    "arrival": "FRA",
                    "incident_type": "denied_boarding",
                    "delay_minutes": None,
                    "compensation": 250.0
                }
            }
            
            scenario_data = scenarios.get(scenario_type, scenarios["delayed_flight"])
            
            claim = await claim_repo.create(
                customer_id=customer.id,
                flight_number=scenario_data["flight_number"],
                flight_date=date.today() - timedelta(days=7),
                departure_airport=scenario_data["departure"],
                arrival_airport=scenario_data["arrival"],
                incident_type=scenario_data["incident_type"],
                delay_minutes=scenario_data["delay_minutes"],
                compensation_amount=scenario_data["compensation"],
                status="submitted",
                description=f"Test scenario: {scenario_type}"
            )
            
            return {
                "success": True,
                "scenario_type": scenario_type,
                "customer_id": str(customer.id),
                "claim_id": str(claim.id),
                "email": email,
                "message": f"Test scenario created: {scenario_type}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to create test scenario"
        }


async def reset_database() -> Dict[str, Any]:
    """Reset database (delete all test data).
    
    WARNING: This deletes all data! Use with caution.
    
    Returns:
        Reset status
    """
    from config import MCPConfig
    
    if not MCPConfig.ENABLE_DESTRUCTIVE_OPS:
        return {
            "success": False,
            "message": "Destructive operations are disabled. Set ENABLE_DESTRUCTIVE_OPS=true"
        }
    
    try:
        async with get_db_session() as session:
            from sqlalchemy import text
            
            # Delete in order to respect foreign keys
            await session.execute(text("DELETE FROM claim_events"))
            await session.execute(text("DELETE FROM claim_notes"))
            await session.execute(text("DELETE FROM claim_status_history"))
            await session.execute(text("DELETE FROM claim_files"))
            await session.execute(text("DELETE FROM claims"))
            await session.execute(text("DELETE FROM customers WHERE email LIKE '%@test.com'"))
            
            await session.commit()
            
            return {
                "success": True,
                "message": "Database reset successfully (test data cleared)"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to reset database"
        }


async def validate_data_integrity() -> Dict[str, Any]:
    """Check for data integrity issues (orphaned records, etc).
    
    Returns:
        Validation report
    """
    try:
        async with get_db_session() as session:
            from sqlalchemy import text
            
            issues = []
            
            # Check for claims without customers
            result = await session.execute(text(
                "SELECT COUNT(*) FROM claims WHERE customer_id NOT IN (SELECT id FROM customers)"
            ))
            orphaned_claims = result.scalar()
            if orphaned_claims > 0:
                issues.append(f"{orphaned_claims} orphaned claims (missing customer)")
            
            # Check for files without claims
            result = await session.execute(text(
                "SELECT COUNT(*) FROM claim_files WHERE claim_id NOT IN (SELECT id FROM claims)"
            ))
            orphaned_files = result.scalar()
            if orphaned_files > 0:
                issues.append(f"{orphaned_files} orphaned files (missing claim)")
            
            return {
                "success": True,
                "integrity_valid": len(issues) == 0,
                "issues": issues if issues else ["No issues found"],
                "message": "Data integrity check complete"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to validate data integrity"
        }
