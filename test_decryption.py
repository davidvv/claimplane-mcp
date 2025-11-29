#!/usr/bin/env python3
"""Test script to verify encryption/decryption functionality."""

import sys
import os
from pathlib import Path

# Add the app directory to the path (using relative path from script location)
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

from app.services.encryption_service import encryption_service

def test_encryption_decryption():
    """Test that encryption and decryption work correctly."""
    # Original test content
    original_content = b"This is a test file for upload/download testing - claim ID 4c8b75c7-b89c-4de8-a1cb-a92aa99af1d1"

    print(f"Original content: {original_content}")
    print(f"Original size: {len(original_content)} bytes")

    # Encrypt the content
    encrypted_content = encryption_service.encrypt_file_content(original_content)
    print(f"Encrypted content: {encrypted_content}")
    print(f"Encrypted size: {len(encrypted_content)} bytes")

    # Decrypt the content
    decrypted_content = encryption_service.decrypt_file_content(encrypted_content)
    print(f"Decrypted content: {decrypted_content}")
    print(f"Decrypted size: {len(decrypted_content)} bytes")

    # Verify integrity
    if original_content == decrypted_content:
        print("✅ SUCCESS: Encryption/Decryption integrity test PASSED")
        return True
    else:
        print("❌ FAILED: Encryption/Decryption integrity test FAILED")
        return False

def test_raw_file_decryption():
    """Test decryption of the raw encrypted file from Nextcloud."""
    try:
        # Read the raw encrypted file
        with open('raw_encrypted_file.txt', 'rb') as f:
            encrypted_data = f.read()

        print(f"Raw encrypted file size: {len(encrypted_data)} bytes")

        # Try to decrypt it
        decrypted_data = encryption_service.decrypt_file_content(encrypted_data)

        print(f"Decrypted content: {decrypted_data}")
        print(f"Decrypted size: {len(decrypted_data)} bytes")

        # Check if it matches our expected content
        expected_content = b"This is a test file for upload/download testing - claim ID 4c8b75c7-b89c-4de8-a1cb-a92aa99af1d1"

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
    test1_passed = test_encryption_decryption()
    print()

    # Test raw file decryption
    test2_passed = test_raw_file_decryption()
    print()

    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        sys.exit(1)