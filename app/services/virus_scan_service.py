"""Virus scanning service using ClamAV."""
import socket
import struct
import logging
import io
from typing import Union, BinaryIO

from app.config import config

logger = logging.getLogger(__name__)

class VirusScanService:
    """Service for scanning files for viruses using ClamAV."""
    
    def __init__(self):
        """Initialize connection parameters."""
        host_port = config.CLAMAV_URL.split(":")
        self.host = host_port[0]
        self.port = int(host_port[1]) if len(host_port) > 1 else 3310
        self.enabled = str(config.VIRUS_SCAN_ENABLED).lower() == "true"

    async def scan_file(self, file_content: bytes) -> bool:
        """
        Scan a file content (bytes) for viruses.
        
        Args:
            file_content: Raw bytes of the file
            
        Returns:
            bool: True if clean, False if infected
            
        Raises:
            Exception: If scanning fails (connection error, etc.)
        """
        if not self.enabled:
            logger.info("Virus scanning is disabled in config")
            return True

        try:
            return self._scan_stream(io.BytesIO(file_content))
        except Exception as e:
            logger.error(f"Virus scan failed: {str(e)}")
            # In high security, we might want to raise error (fail closed)
            # For now, we log error and raise it so upload fails safely
            raise Exception(f"Virus scan service unavailable: {str(e)}")

    def _scan_stream(self, stream: BinaryIO) -> bool:
        """
        Send stream to ClamAV via TCP socket (zINSTREAM protocol).
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(30.0)  # 30 second timeout
        
        try:
            s.connect((self.host, self.port))
            
            # Send zINSTREAM command
            s.send(b"zINSTREAM\0")
            
            chunk_size = 4096
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                
                # Send chunk length (4 bytes network byte order)
                s.send(struct.pack("!I", len(chunk)))
                # Send chunk data
                s.send(chunk)
            
            # Send zero length to indicate end of stream
            s.send(struct.pack("!I", 0))
            
            # Read response
            response = s.recv(1024).strip()
            logger.info(f"ClamAV scan result: {response}")
            
            # Check response
            if b"stream: OK" in response:
                return True
            elif b"FOUND" in response:
                logger.warning(f"Virus detected: {response.decode('utf-8', errors='ignore')}")
                return False
            else:
                logger.error(f"Unexpected ClamAV response: {response}")
                raise Exception("Unexpected response from antivirus")
                
        except socket.error as e:
            logger.error(f"ClamAV connection error: {e}")
            raise Exception("Could not connect to antivirus service")
        finally:
            s.close()

# Global instance
virus_scan_service = VirusScanService()
