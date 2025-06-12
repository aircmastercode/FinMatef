"""
Base agent class for all agents in the system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import uuid
import time

logger = logging.getLogger(__name__)

class Agent(ABC):
    """
    Base class for all agents in the system.
    
    Each agent should implement the process method to handle its specific tasks.
    """
    
    def __init__(self):
        """Initialize the agent with a name derived from its class."""
        self.name = self.__class__.__name__
        self.id = str(uuid.uuid4())
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return a response.
        
        Args:
            input_data: The input data to process.
            context: Additional context information.
            
        Returns:
            Dict[str, Any]: The processed result.
        """
        pass
    
    async def run(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent, logging activity and measuring performance.
        
        This method wraps the process method with logging and performance tracking.
        
        Args:
            input_data: The input data to process.
            context: Additional context information.
            
        Returns:
            Dict[str, Any]: The processed result.
        """
        start_time = time.time()
        
        try:
            logger.info(f"Agent {self.name} starting processing")
            result = await self.process(input_data, context)
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Log activity
            await self.log_activity(input_data, result, processing_time)
            
            logger.info(f"Agent {self.name} completed in {processing_time:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Agent {self.name} failed: {str(e)}", exc_info=True)
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Log failure
            await self.log_activity(
                input_data,
                {"status": "error", "error": str(e)},
                processing_time
            )
            
            # Re-raise the exception
            raise
    
    async def log_activity(self, input_data: Dict[str, Any], output_data: Dict[str, Any], processing_time: float) -> None:
        """
        Log agent activity for monitoring and debugging.
        
        Args:
            input_data: The input data processed.
            output_data: The output data produced.
            processing_time: The time taken to process in seconds.
        """
        # Default implementation logs to the console
        logger.debug(
            f"Agent {self.name} activity:\n"
            f"  Input: {self._safe_repr(input_data)}\n"
            f"  Output: {self._safe_repr(output_data)}\n"
            f"  Processing time: {processing_time:.2f}s"
        )
        
        # In a production system, this could log to a database or monitoring service
    
    def _safe_repr(self, data: Any) -> str:
        """
        Create a safe string representation of data, truncating if too large.
        
        Args:
            data: The data to represent as a string.
            
        Returns:
            str: A string representation of the data.
        """
        try:
            repr_str = str(data)
            if len(repr_str) > 500:
                return repr_str[:500] + "..."
            return repr_str
        except Exception:
            return "<unprintable>" 