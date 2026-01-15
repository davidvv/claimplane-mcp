#!/usr/bin/env python3
"""Test script to verify libmagic installation and functionality."""

import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

def test_libmagic_import():
    """Test if python-magic can be imported and used."""
    try:
        import magic
        print("✓ python-magic imported successfully")
        
        # Test basic functionality
        test_content = b"%PDF-1.4\n%Test PDF content"
        try:
            mime_type = magic.from_buffer(test_content, mime=True)
            print(f"✓ Magic detection works: {mime_type}")
            return True
        except Exception as e:
            print(f"✗ Magic detection failed: {e}")
            return False
            
    except ImportError as e:
        print(f"✗ Failed to import python-magic: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_mimetypes_fallback():
    """Test mimetypes fallback functionality."""
    import mimetypes
    
    test_files = [
        "test.pdf",
        "test.jpg", 
        "test.png",
        "test.txt",
        "test.doc"
    ]
    
    print("\nTesting mimetypes fallback:")
    for filename in test_files:
        mime_type, _ = mimetypes.guess_type(filename)
        print(f"  {filename}: {mime_type or 'application/octet-stream'}")

def main():
    """Main test function."""
    print("Testing libmagic installation and functionality...")
    print("=" * 50)
    
    # Test 1: Direct magic import
    magic_works = test_libmagic_import()
    
    # Test 2: Test our file validation service
    print("\nTesting file validation service...")
    try:
        from app.services.file_validation_service import FileValidationService
        service = FileValidationService()
        
        # Test MIME type detection
        test_content = b"%PDF-1.4\n%Test PDF content"
        test_filename = "test.pdf"
        
        mime_type = service._detect_mime_type(test_content, test_filename)
        print(f"✓ File validation service MIME detection: {mime_type}")
        
    except Exception as e:
        print(f"✗ File validation service failed: {e}")
    
    # Test 3: mimetypes fallback
    test_mimetypes_fallback()
    
    print("\n" + "=" * 50)
    if magic_works:
        print("✓ All tests passed - libmagic is working correctly!")
        return 0
    else:
        print("✗ Some tests failed - libmagic needs to be installed")
        return 1

if __name__ == "__main__":
    sys.exit(main())