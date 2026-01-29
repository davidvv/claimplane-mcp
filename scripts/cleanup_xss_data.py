#!/usr/bin/env python3
"""
Database cleanup script to remove XSS payloads from customer data.
This script sanitizes existing customer names that may contain HTML tags.

Run this script to clean up existing XSS vulnerabilities after deploying the fix.
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import update
from sqlalchemy.future import select
from app.database import async_session_maker
from app.models import Customer


def sanitize_html(value: str) -> str:
    """Remove HTML tags from string."""
    if not value:
        return value
    import re
    clean = re.sub(r'<[^>]+>', '', value)
    return clean


async def cleanup_xss_data():
    """Find and clean customers with HTML in their names."""
    print("=" * 60)
    print("XSS Data Cleanup Script")
    print("=" * 60)
    
    cleaned_count = 0
    
    async with async_session_maker() as session:
        # Find all customers
        result = await session.execute(select(Customer))
        customers = result.scalars().all()
        
        print(f"\nChecking {len(customers)} customers for XSS payloads...")
        
        for customer in customers:
            original_first = customer.first_name
            original_last = customer.last_name
            
            # Sanitize names
            clean_first = sanitize_html(original_first) if original_first else original_first
            clean_last = sanitize_html(original_last) if original_last else original_last
            
            # Check if cleaning was needed
            if clean_first != original_first or clean_last != original_last:
                print(f"\n⚠️  Found XSS payload in customer: {customer.email}")
                print(f"   First name: '{original_first}' -> '{clean_first}'")
                print(f"   Last name: '{original_last}' -> '{clean_last}'")
                
                # Update the customer
                customer.first_name = clean_first
                customer.last_name = clean_last
                cleaned_count += 1
        
        if cleaned_count > 0:
            await session.commit()
            print(f"\n✅ Cleaned {cleaned_count} customer(s) with XSS payloads")
        else:
            print("\n✅ No XSS payloads found in customer data")
    
    print("\n" + "=" * 60)
    print("Cleanup complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(cleanup_xss_data())