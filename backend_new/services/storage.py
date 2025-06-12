"""
Storage Service for file management.

This service provides interfaces for storing and retrieving files,
including uploads from users, processed documents, and other assets.
"""
import os
import uuid
import logging
import shutil
from typing import Dict, Any, List, Optional, BinaryIO, Union
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class StorageService:
    """Service for managing file storage."""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize the storage service.
        
        Args:
            base_dir: Base directory for file storage. Defaults to './uploads'.
        """
        self.base_dir = Path(base_dir or "./uploads")
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure the required directories exist."""
        for dir_name in ["documents", "audio", "temp"]:
            directory = self.base_dir / dir_name
            os.makedirs(directory, exist_ok=True)
    
    async def save_document(
        self, file: BinaryIO, filename: Optional[str] = None, category: str = "documents"
    ) -> Dict[str, Any]:
        """
        Save a document file to storage.
        
        Args:
            file: File handle
            filename: Optional filename (if not provided, a UUID will be generated)
            category: File category (documents, audio, temp, etc.)
            
        Returns:
            Dict[str, Any]: File metadata
        """
        try:
            # Generate filename if not provided
            if not filename:
                ext = ".bin"
                if hasattr(file, "filename"):
                    ext = os.path.splitext(file.filename)[1]
                filename = f"{uuid.uuid4()}{ext}"
            
            # Ensure category directory exists
            category_dir = self.base_dir / category
            os.makedirs(category_dir, exist_ok=True)
            
            # Full path to save the file
            file_path = category_dir / filename
            
            # Save the file
            file.seek(0)
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file, f)
            
            # File metadata
            metadata = {
                "id": str(uuid.uuid4()),
                "filename": filename,
                "path": str(file_path),
                "category": category,
                "created_at": datetime.now().isoformat(),
            }
            
            logger.info(f"Saved file: {filename} to {category}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise
    
    async def get_file(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        Get a file path from storage.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[Path]: Path to the file or None if not found
        """
        try:
            path = Path(file_path)
            if path.is_absolute():
                # If absolute path, check if it's within the base directory
                if not str(path).startswith(str(self.base_dir)):
                    logger.warning(f"Attempted to access file outside base directory: {path}")
                    return None
            else:
                # If relative path, resolve against base directory
                path = self.base_dir / path
            
            if not path.exists():
                logger.warning(f"File not found: {path}")
                return None
                
            return path
            
        except Exception as e:
            logger.error(f"Error getting file: {str(e)}")
            return None
    
    async def delete_file(self, file_path: Union[str, Path]) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            path = await self.get_file(file_path)
            if not path:
                return False
                
            os.remove(path)
            logger.info(f"Deleted file: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    async def list_files(self, category: str = None) -> List[Dict[str, Any]]:
        """
        List files in storage.
        
        Args:
            category: Optional category filter
            
        Returns:
            List[Dict[str, Any]]: List of file metadata
        """
        try:
            result = []
            
            # Determine which directories to scan
            dirs = []
            if category:
                category_dir = self.base_dir / category
                if category_dir.exists():
                    dirs = [category_dir]
                else:
                    logger.warning(f"Category directory not found: {category}")
                    return []
            else:
                dirs = [d for d in self.base_dir.iterdir() if d.is_dir() and d.name != "temp"]
            
            # Scan directories
            for dir_path in dirs:
                for file_path in dir_path.iterdir():
                    if file_path.is_file():
                        result.append({
                            "filename": file_path.name,
                            "path": str(file_path),
                            "category": dir_path.name,
                            "size": file_path.stat().st_size,
                            "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                        })
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return [] 