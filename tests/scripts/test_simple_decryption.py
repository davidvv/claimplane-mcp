#!/usr/bin/env python3
"""Simple test script to verify encryption/decryption functionality."""

import base64
import os
import sys
from pathlib import Path

# Add the app directory to the path (using relative path from script location)
script_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(script_dir))

def test_basic_encryption():
    """Test basic encryption/decryption without full app context."""
    try:
        # Import only what we need
        from cryptography.fernet import Fernet

        # Use the same key as the application
        key = 'cz4qKNRg3SdNzRLuPRIXpc3muCpbncZQezeVYknj84Q='
        fernet = Fernet(key.encode())

        # Original test content
        original_content = b"This is a test file for upload/download testing - claim ID 4c8b75c7-b89c-4de8-a1cb-a92aa99af1d1"

        print(f"Original content: {original_content}")
        print(f"Original size: {len(original_content)} bytes")

        # Encrypt the content
        encrypted_content = fernet.encrypt(original_content)
        print(f"Encrypted content: {encrypted_content}")
        print(f"Encrypted size: {len(encrypted_content)} bytes")

        # Decrypt the content
        decrypted_content = fernet.decrypt(encrypted_content)
        print(f"Decrypted content: {decrypted_content}")
        print(f"Decrypted size: {len(decrypted_content)} bytes")

        # Verify integrity
        if original_content == decrypted_content:
            print("✅ SUCCESS: Basic encryption/decryption test PASSED")
            return True, fernet
        else:
            print("❌ FAILED: Basic encryption/decryption test FAILED")
            return False, None

    except Exception as e:
        print(f"❌ ERROR: Basic encryption test failed: {e}")
        return False, None

def test_raw_file_decryption(fernet):
    """Test decryption of the raw encrypted file from Nextcloud."""
    try:
        # Read the raw encrypted file
        with open('raw_encrypted_file.txt', 'rb') as f:
            encrypted_data = f.read()

        print(f"Raw encrypted file size: {len(encrypted_data)} bytes")

        # Try to decrypt it
        decrypted_data = fernet.decrypt(encrypted_data)

        print(f"Decrypted content: {decrypted_data}")
        print(f"Decrypted size: {len(decrypted_data)} bytes")

        # Check if it matches our expected content (should be the small test file with newline)
        expected_content = b"This is a test file for upload/download testing - claim ID 4c8b75c7-b89c-4de8-a1cb-a92aa99af1d1\n"

        if decrypted_data == expected_content:
            print("✅ SUCCESS: Raw file decryption test PASSED")
            return True
        else:
            print("❌ WARNING: Decrypted content doesn't match expected content")
            print(f"Expected: {expected_content}")
            print(f"Got:      {decrypted_data}")
            return False

    except Exception as e:
        print(f"❌ ERROR: Failed to decrypt raw file: {e}")
        return False

if __name__ == "__main__":
    print("Testing encryption/decryption functionality...")
    print("=" * 50)

    # Test basic encryption/decryption
    test1_passed, fernet = test_basic_encryption()
    print()

    if test1_passed and fernet:
        # Test raw file decryption
        test2_passed = test_raw_file_decryption(fernet)
        print()

        if test2_passed:
            print("🎉 ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print("❌ RAW FILE DECRYPTION FAILED!")
            sys.exit(1)
    else:
        print("❌ BASIC ENCRYPTION TEST FAILED!")
        sys.exit(1)