"""
User Database Client - Handles user data storage and retrieval.

This module provides a client for interacting with the user database.
"""
import logging
import os
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class UserDBClient:
    """
    Client for interacting with the user database.
    
    This client provides methods for storing and retrieving user data.
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the user database client.
        
        Args:
            data_dir: Directory for storing user data
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # Create subdirectories
        self.users_dir = os.path.join(data_dir, "users")
        self.sessions_dir = os.path.join(data_dir, "sessions")
        self.escalations_dir = os.path.join(data_dir, "escalations")
        
        os.makedirs(self.users_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        os.makedirs(self.escalations_dir, exist_ok=True)
        
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data.
        
        Args:
            user_id: User identifier
            
        Returns:
            Optional[Dict[str, Any]]: User data or None if not found
        """
        user_path = os.path.join(self.users_dir, f"{user_id}.json")
        
        if not os.path.exists(user_path):
            return None
            
        try:
            with open(user_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading user data: {str(e)}")
            return None
            
    async def create_user(self, user_data: Dict[str, Any]) -> bool:
        """
        Create a new user.
        
        Args:
            user_data: User data
            
        Returns:
            bool: True if successful, False otherwise
        """
        user_id = user_data.get("id")
        if not user_id:
            logger.error("User ID is required")
            return False
            
        user_path = os.path.join(self.users_dir, f"{user_id}.json")
        
        try:
            with open(user_path, "w") as f:
                json.dump(user_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False
            
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Update user data.
        
        Args:
            user_id: User identifier
            user_data: Updated user data
            
        Returns:
            bool: True if successful, False otherwise
        """
        user_path = os.path.join(self.users_dir, f"{user_id}.json")
        
        if not os.path.exists(user_path):
            return False
            
        try:
            with open(user_path, "w") as f:
                json.dump(user_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return False

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user's profile data.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: User profile data
        """
        user_data = await self.get_user(user_id)
        
        # Remove sensitive or internal fields
        if "error" in user_data:
            return {"id": user_id, "error": user_data["error"]}
        
        return {
            "id": user_data.get("id"),
            "created_at": user_data.get("created_at"),
            "last_active": user_data.get("last_active"),
            "preferences": user_data.get("preferences", {}),
            "metadata": user_data.get("metadata", {})
        }
    
    async def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update a user's profile.
        
        Args:
            user_id: User ID
            profile_data: Profile data to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Filter out fields that shouldn't be directly updated
        safe_data = {k: v for k, v in profile_data.items() 
                    if k not in ["id", "created_at"]}
        
        return await self.update_user(user_id, safe_data)
    
    async def set_preference(self, user_id: str, key: str, value: Any) -> bool:
        """
        Set a user preference.
        
        Args:
            user_id: User ID
            key: Preference key
            value: Preference value
            
        Returns:
            bool: True if successful, False otherwise
        """
        user_data = await self.get_user(user_id)
        if "preferences" not in user_data:
            user_data["preferences"] = {}
        user_data["preferences"][key] = value
        return await self.update_user(user_id, user_data)
    
    async def get_conversation_history(
        self, user_id: str, session_id: Optional[str] = None, 
        limit: int = 10, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User ID
            session_id: Optional session ID to filter by
            limit: Maximum number of messages to retrieve
            skip: Number of messages to skip
            
        Returns:
            List[Dict[str, Any]]: Conversation history
        """
        user_data = await self.get_user(user_id)
        if "history" not in user_data:
            return []
        
        history = user_data["history"]
        
        # Filter by session if provided
        if session_id:
            history = [msg for msg in history if msg.get("session_id") == session_id]
        
        # Apply skip and limit
        return history[skip:skip + limit] if skip < len(history) else []
    
    async def add_message(
        self, user_id: str, content: str, role: str = "user",
        session_id: Optional[str] = None, metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a message to the conversation history.
        
        Args:
            user_id: User ID
            content: Message content
            role: Message role (user or assistant)
            session_id: Session ID
            metadata: Additional metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        user_data = await self.get_user(user_id)
        if "history" not in user_data:
            user_data["history"] = []
        
        message = {
            "user_id": user_id,
            "content": content,
            "role": role,
            "timestamp": datetime.datetime.now().isoformat(),
            "session_id": session_id or str(uuid.uuid4()),
            "metadata": metadata or {}
        }
        
        user_data["history"].append(message)
        return await self.update_user(user_id, user_data)
    
    async def clear_history(self, user_id: str) -> bool:
        """
        Clear conversation history for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        user_data = await self.get_user(user_id)
        if "history" not in user_data:
            return True
        
        user_data["history"] = []
        return await self.update_user(user_id, user_data) 