"""Nextcloud integration service for file storage."""
import base64
import json
import os
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import httpx
from fastapi import HTTPException, status

from app.config import config


class NextcloudService:
    """Service for integrating with Nextcloud WebDAV and OCS APIs."""
    
    def __init__(self):
        """Initialize Nextcloud service with configuration."""
        self.base_url = config.NEXTCLOUD_URL
        self.username = config.NEXTCLOUD_USERNAME
        self.password = config.NEXTCLOUD_PASSWORD
        self.timeout = config.NEXTCLOUD_TIMEOUT
        
        # WebDAV base URL
        self.webdav_url = urljoin(self.base_url, "/remote.php/dav/files/")
        
        # OCS API base URL
        self.ocs_url = urljoin(self.base_url, "/ocs/v2.php/")
        
        # Basic auth credentials
        self.auth = (self.username, self.password)
        
        # OCS API headers
        self.ocs_headers = {
            "OCS-APIRequest": "true",
            "Content-Type": "application/json"
        }
    
    async def upload_file(self, file_content: bytes, remote_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """Upload file to Nextcloud via WebDAV."""
        try:
            # Construct full WebDAV URL
            full_path = f"{self.username}/{remote_path.lstrip('/')}"
            upload_url = urljoin(self.webdav_url, full_path)
            
            # Set headers
            headers = {
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(file_content))
            }
            
            # Upload file
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                method = "PUT" if overwrite else "PUT"
                response = await client.request(
                    method=method,
                    url=upload_url,
                    content=file_content,
                    headers=headers,
                    auth=self.auth
                )
                
                if response.status_code not in [200, 201, 204]:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Nextcloud upload failed: {response.status_code} - {response.text}"
                    )
                
                return {
                    "success": True,
                    "file_id": remote_path,
                    "url": upload_url,
                    "status_code": response.status_code
                }
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Nextcloud connection error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Nextcloud upload error: {str(e)}"
            )
    
    async def download_file(self, remote_path: str) -> bytes:
        """Download file from Nextcloud via WebDAV."""
        try:
            # Construct full WebDAV URL
            full_path = f"{self.username}/{remote_path.lstrip('/')}"
            download_url = urljoin(self.webdav_url, full_path)
            
            # Download file
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url=download_url,
                    auth=self.auth
                )
                
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="File not found in Nextcloud"
                    )
                elif response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Nextcloud download failed: {response.status_code}"
                    )
                
                return response.content
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Nextcloud connection error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Nextcloud download error: {str(e)}"
            )
    
    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from Nextcloud via WebDAV."""
        try:
            # Construct full WebDAV URL
            full_path = f"{self.username}/{remote_path.lstrip('/')}"
            delete_url = urljoin(self.webdav_url, full_path)
            
            # Delete file
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    url=delete_url,
                    auth=self.auth
                )
                
                if response.status_code == 404:
                    return False  # File didn't exist
                elif response.status_code not in [200, 204]:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Nextcloud delete failed: {response.status_code}"
                    )
                
                return True
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Nextcloud connection error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Nextcloud delete error: {str(e)}"
            )
    
    async def create_share(self, path: str, share_type: int = 3, permissions: int = 1) -> Dict[str, Any]:
        """Create a share link for a file."""
        try:
            share_url = urljoin(self.ocs_url, "apps/files_sharing/api/v1/shares")
            
            data = {
                "path": path,
                "shareType": share_type,  # 3 = public link
                "permissions": permissions,  # 1 = read
                "password": "",  # Optional password protection
                "expireDate": ""  # Optional expiration date
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=share_url,
                    json=data,
                    headers=self.ocs_headers,
                    auth=self.auth
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Nextcloud share creation failed: {response.status_code}"
                    )
                
                # Parse OCS response
                share_data = response.json()
                return share_data
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Nextcloud connection error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Nextcloud share error: {str(e)}"
            )
    
    async def get_file_info(self, remote_path: str) -> Dict[str, Any]:
        """Get file information from Nextcloud."""
        try:
            # Use WebDAV PROPFIND to get file properties
            full_path = f"{self.username}/{remote_path.lstrip('/')}"
            propfind_url = urljoin(self.webdav_url, full_path)
            
            # PROPFIND request body
            propfind_body = """<?xml version="1.0" encoding="utf-8"?>
            <D:propfind xmlns:D="DAV:">
                <D:prop>
                    <D:getcontentlength/>
                    <D:getcontenttype/>
                    <D:getlastmodified/>
                    <D:creationdate/>
                </D:prop>
            </D:propfind>"""
            
            headers = {
                "Content-Type": "application/xml",
                "Depth": "0"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method="PROPFIND",
                    url=propfind_url,
                    content=propfind_body,
                    headers=headers,
                    auth=self.auth
                )
                
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="File not found in Nextcloud"
                    )
                elif response.status_code != 207:  # 207 Multi-Status for PROPFIND
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Nextcloud PROPFIND failed: {response.status_code}"
                    )
                
                # Parse XML response (simplified)
                # In a real implementation, you'd parse the XML properly
                return {
                    "path": remote_path,
                    "exists": True,
                    "status_code": response.status_code
                }
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Nextcloud connection error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Nextcloud file info error: {str(e)}"
            )
    
    async def test_connection(self) -> bool:
        """Test connection to Nextcloud."""
        try:
            # Try to get status.php
            status_url = urljoin(self.base_url, "/status.php")
            
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(status_url)
                
                if response.status_code == 200:
                    status_data = response.json()
                    return status_data.get("installed", False)
                
                return False
                
        except Exception:
            return False


# Global Nextcloud service instance
nextcloud_service = NextcloudService()