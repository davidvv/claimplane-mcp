#!/usr/bin/env python3
"""Test script for Nextcloud integration."""
import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.nextcloud_service import nextcloud_service


async def test_nextcloud_connection():
    """Test basic Nextcloud connection."""
    print("Testing Nextcloud connection...")
    
    try:
        is_connected = await nextcloud_service.test_connection()
        if is_connected:
            print("✅ Nextcloud connection successful")
            return True
        else:
            print("❌ Nextcloud connection failed")
            return False
    except Exception as e:
        print(f"❌ Nextcloud connection error: {e}")
        return False


async def test_file_upload():
    """Test file upload to Nextcloud."""
    print("\nTesting file upload...")
    
    try:
        test_content = b"Test file content for flight claim system"
        test_filename = "test_upload.txt"
        
        result = await nextcloud_service.upload_file(
            file_content=test_content,
            remote_path=f"test/{test_filename}"
        )
        
        if result["success"]:
            print(f"✅ File upload successful: {result}")
            return result
        else:
            print(f"❌ File upload failed: {result}")
            return None
            
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return None


async def test_file_download():
    """Test file download from Nextcloud."""
    print("\nTesting file download...")
    
    try:
        # First upload a file
        test_content = b"Test download content"
        test_filename = "test_download.txt"
        
        upload_result = await nextcloud_service.upload_file(
            file_content=test_content,
            remote_path=f"test/{test_filename}"
        )
        
        if not upload_result["success"]:
            print("❌ Cannot test download - upload failed")
            return False
        
        # Now download it
        downloaded_content = await nextcloud_service.download_file(
            remote_path=f"test/{test_filename}"
        )
        
        if downloaded_content == test_content:
            print("✅ File download successful - content matches")
            return True
        else:
            print("❌ File download failed - content mismatch")
            return False
            
    except Exception as e:
        print(f"❌ File download error: {e}")
        return False


async def test_file_delete():
    """Test file deletion from Nextcloud."""
    print("\nTesting file deletion...")
    
    try:
        # First upload a file
        test_content = b"Test delete content"
        test_filename = "test_delete.txt"
        
        upload_result = await nextcloud_service.upload_file(
            file_content=test_content,
            remote_path=f"test/{test_filename}"
        )
        
        if not upload_result["success"]:
            print("❌ Cannot test delete - upload failed")
            return False
        
        # Now delete it
        delete_success = await nextcloud_service.delete_file(
            remote_path=f"test/{test_filename}"
        )
        
        if delete_success:
            print("✅ File deletion successful")
            return True
        else:
            print("❌ File deletion failed")
            return False
            
    except Exception as e:
        print(f"❌ File deletion error: {e}")
        return False


async def test_file_info():
    """Test getting file information from Nextcloud."""
    print("\nTesting file info retrieval...")
    
    try:
        # First upload a file
        test_content = b"Test info content"
        test_filename = "test_info.txt"
        
        upload_result = await nextcloud_service.upload_file(
            file_content=test_content,
            remote_path=f"test/{test_filename}"
        )
        
        if not upload_result["success"]:
            print("❌ Cannot test info - upload failed")
            return False
        
        # Get file info
        file_info = await nextcloud_service.get_file_info(
            remote_path=f"test/{test_filename}"
        )
        
        if file_info["exists"]:
            print(f"✅ File info retrieved: {file_info}")
            return True
        else:
            print("❌ File info retrieval failed")
            return False
            
    except Exception as e:
        print(f"❌ File info error: {e}")
        return False


async def test_share_creation():
    """Test share link creation in Nextcloud."""
    print("\nTesting share creation...")
    
    try:
        # First upload a file
        test_content = b"Test share content"
        test_filename = "test_share.txt"
        
        upload_result = await nextcloud_service.upload_file(
            file_content=test_content,
            remote_path=f"test/{test_filename}"
        )
        
        if not upload_result["success"]:
            print("❌ Cannot test share - upload failed")
            return False
        
        # Create share
        share_result = await nextcloud_service.create_share(
            path=f"test/{test_filename}",
            share_type=3,  # Public link
            permissions=1  # Read only
        )
        
        if share_result:
            print(f"✅ Share created successfully: {share_result}")
            return True
        else:
            print("❌ Share creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Share creation error: {e}")
        return False


async def cleanup_test_files():
    """Clean up test files from Nextcloud."""
    print("\nCleaning up test files...")
    
    test_files = [
        "test/test_upload.txt",
        "test/test_download.txt",
        "test/test_delete.txt",
        "test/test_info.txt",
        "test/test_share.txt"
    ]
    
    deleted_count = 0
    
    for file_path in test_files:
        try:
            success = await nextcloud_service.delete_file(file_path)
            if success:
                deleted_count += 1
                print(f"✅ Deleted: {file_path}")
            else:
                print(f"⚠️  File not found (already deleted): {file_path}")
        except Exception as e:
            print(f"⚠️  Error deleting {file_path}: {e}")
    
    print(f"✅ Cleanup completed. Deleted {deleted_count} files.")


async def main():
    """Main test function."""
    print("🚀 Starting Nextcloud Integration Tests")
    print("=" * 50)
    
    # Check if Nextcloud is configured
    if not os.getenv("NEXTCLOUD_URL"):
        print("❌ NEXTCLOUD_URL environment variable not set")
        print("Please set NEXTCLOUD_URL, NEXTCLOUD_USERNAME, and NEXTCLOUD_PASSWORD")
        return
    
    # Test connection
    connection_success = await test_nextcloud_connection()
    if not connection_success:
        print("❌ Cannot proceed with tests - Nextcloud connection failed")
        return
    
    # Run all tests
    tests = [
        test_file_upload,
        test_file_download,
        test_file_delete,
        test_file_info,
        test_share_creation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    # Cleanup
    await cleanup_test_files()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Nextcloud integration is working correctly.")
    else:
        print(f"\n⚠️  {failed} tests failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main())