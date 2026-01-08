#!/usr/bin/env python3
"""
Debug script to test AeroDataBox API connection and see raw responses.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import httpx
from app.config import config
from app.services.aerodatabox_service import aerodatabox_service


async def test_api_connection():
    """Test basic API connection and response format."""

    print(f"\n{'='*80}")
    print(f"TESTING AERODATABOX API CONNECTION")
    print(f"{'='*80}\n")

    print(f"Base URL: {config.AERODATABOX_BASE_URL}")
    print(f"API Key configured: {'Yes' if config.AERODATABOX_API_KEY else 'No'}")
    print(f"API Key (first 10 chars): {config.AERODATABOX_API_KEY[:10]}..." if config.AERODATABOX_API_KEY else "")
    print(f"Timeout: {config.AERODATABOX_TIMEOUT}s")
    print(f"Max Retries: {config.AERODATABOX_MAX_RETRIES}\n")

    # Test with a recent known flight (British Airways 303 is a daily flight)
    test_flight = "BA303"
    test_date = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")

    print(f"Testing with: {test_flight} on {test_date}\n")

    # Build the URL
    url = f"{config.AERODATABOX_BASE_URL}/flights/number/{test_flight}/{test_date}"
    print(f"Full URL: {url}\n")

    # Get headers
    headers = aerodatabox_service._get_headers()
    print(f"Headers:")
    for key, value in headers.items():
        if 'key' in key.lower():
            print(f"  {key}: {value[:10]}..." if len(value) > 10 else f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")

    print(f"\n{'='*80}")
    print(f"MAKING REQUEST...")
    print(f"{'='*80}\n")

    try:
        async with httpx.AsyncClient(timeout=config.AERODATABOX_TIMEOUT) as client:
            response = await client.get(url, headers=headers)

            print(f"Status Code: {response.status_code}")
            print(f"Response Headers:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")

            print(f"\nRaw Response Body (first 500 chars):")
            print(f"{'-'*80}")
            raw_text = response.text
            print(raw_text[:500])
            if len(raw_text) > 500:
                print(f"\n... ({len(raw_text) - 500} more characters)")
            print(f"{'-'*80}\n")

            # Try to parse as JSON
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ Successfully parsed JSON response")
                    print(f"Response type: {type(data)}")
                    if isinstance(data, list):
                        print(f"Number of flights: {len(data)}")
                    print(f"\nParsed Response:")
                    import json
                    print(json.dumps(data, indent=2)[:1000])
                except Exception as e:
                    print(f"❌ Failed to parse JSON: {str(e)}")
            else:
                print(f"❌ HTTP Error {response.status_code}")
                print(f"Response: {raw_text}")

    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api_connection())
