"""Test script to verify UA988 (FRA-IAD) distance calculation works."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.compensation_service import CompensationService


async def test_ua988_route():
    """Test FRA-IAD route (UA988) with AeroDataBox integration."""

    print("=" * 80)
    print("Testing UA988 Route: Frankfurt (FRA) → Washington Dulles (IAD)")
    print("=" * 80)

    # Test 1: Try with AeroDataBox API (if configured)
    print("\n1. Testing with AeroDataBox API (use_api=True):")
    print("-" * 80)
    try:
        distance_api = await CompensationService.calculate_distance(
            "FRA", "IAD", use_api=True
        )
        if distance_api:
            print(f"✓ SUCCESS: Distance calculated via API: {distance_api:.2f} km")
        else:
            print("✗ FAILED: API returned None (likely not configured or failed)")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")

    # Test 2: Try with hardcoded coordinates only
    print("\n2. Testing with hardcoded coordinates (use_api=False):")
    print("-" * 80)
    try:
        distance_hardcoded = await CompensationService.calculate_distance(
            "FRA", "IAD", use_api=False
        )
        if distance_hardcoded:
            print(f"✓ SUCCESS: Distance calculated via hardcoded: {distance_hardcoded:.2f} km")
        else:
            print("✗ EXPECTED: IAD not in hardcoded list, returned None")
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")

    # Test 3: Full compensation calculation with 4-hour delay
    print("\n3. Testing full compensation calculation (4-hour delay):")
    print("-" * 80)
    try:
        result = await CompensationService.calculate_compensation(
            departure_airport="FRA",
            arrival_airport="IAD",
            delay_hours=4.0,
            incident_type="delay",
            use_api=True  # Try API first
        )

        print(f"   Eligible: {result['eligible']}")
        print(f"   Amount: €{result['amount']}")
        print(f"   Distance: {result['distance_km']:.2f} km")
        print(f"   Reason: {result['reason']}")
        print(f"   Manual Review: {result['requires_manual_review']}")

        if result['eligible'] and result['distance_km'] > 0:
            print("\n✓ SUCCESS: UA988 route now works! Compensation calculated successfully.")
        elif result['requires_manual_review'] and "coordinates not found" in result['reason']:
            print("\n✗ ISSUE: Still unable to find coordinates (API may not be configured)")
        else:
            print(f"\n⚠ PARTIAL: Got result but check details above")

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("Expected distance: ~6,584 km (FRA-IAD)")
    print("Expected compensation tier: Long haul (>3,500 km) = €600")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_ua988_route())
