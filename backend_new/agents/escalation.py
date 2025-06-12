"""
Escalation Agent - Handle queries that require human intervention.

This agent determines when to escalate queries to human operators
and manages the escalation workflow.
"""
import logging
from typing import Dict, Any, List, Optional

from .base import Agent
from services.llm import LLMService
from services.memory import MemoryService

logger = logging.getLogger(__name__)

class EscalationAgent(Agent):
    """
    Agent for handling escalations to human operators.
    
    This agent evaluates whether a query needs escalation,
    manages the escalation process, and bridges between
    the AI system and human operators.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        memory_service: MemoryService,
    ):
        """
        Initialize the escalation agent.
        
        Args:
            llm_service: Service for language model processing
            memory_service: Service for handling conversation memory
        """
        super().__init__()
        self.llm_service = llm_service
        self.memory_service = memory_service
    
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an escalation request.
        
        Args:
            input_data: Input data containing query and response information
            context: Additional context including user_id, session_id
            
        Returns:
            Dict[str, Any]: Escalation result
        """
        query = input_data.get("query", "")
        response = input_data.get("response", "")
        confidence = input_data.get("confidence", 0.0)
        needs_escalation = input_data.get("needs_escalation", False)
        escalation_reason = input_data.get("escalation_reason", "")
        user_id = context.get("user_id")
        session_id = context.get("session_id")
        
        if not query:
            logger.error("No query provided for escalation evaluation")
            return {
                "status": "error",
                "message": "No query provided for escalation evaluation"
            }
        
        try:
            # If not already marked for escalation, evaluate if escalation is needed
            if not needs_escalation:
                evaluation = await self._evaluate_escalation(query, response, confidence)
                needs_escalation = evaluation["needs_escalation"]
                escalation_reason = evaluation["reason"]
            
            if needs_escalation:
                # Handle the escalation process
                escalation_result = await self._handle_escalation(
                    query, response, escalation_reason, user_id, session_id
                )
                
                return {
                    "status": "success",
                    "needs_escalation": True,
                    "escalation_id": escalation_result.get("escalation_id", ""),
                    "interim_response": escalation_result.get("interim_response", ""),
                    "escalation_reason": escalation_reason,
                    "estimated_wait_time": escalation_result.get("estimated_wait_time", 0)
                }
            else:
                # No escalation needed
                return {
                    "status": "success",
                    "needs_escalation": False,
                    "message": "No escalation required"
                }
                
        except Exception as e:
            logger.error(f"Error processing escalation: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing escalation: {str(e)}"
            }
    
    async def _evaluate_escalation(
        self, query: str, response: str, confidence: float
    ) -> Dict[str, Any]:
        """
        Evaluate whether a query should be escalated to a human operator.
        
        Args:
            query: User query
            response: AI-generated response
            confidence: Confidence level of the response
            
        Returns:
            Dict[str, Any]: Evaluation result
        """
        # Check confidence threshold for automatic escalation
        if confidence < 0.6:
            return {
                "needs_escalation": True,
                "reason": f"Low confidence response ({confidence:.2f} < 0.6)"
            }
        
        # Use LLM to analyze if this query needs human attention
        system_prompt = {
            "role": "system",
            "content": """You are an escalation analyst for LenDen Club's AI assistant.
Your task is to determine whether a user query and its AI-generated response requires human intervention.

Escalate to a human operator for these situations:
1. Complex or nuanced financial questions beyond the AI's capabilities
2. Questions about specific user accounts or transactions
3. Requests requiring user authentication or verification
4. Legal questions or regulatory issues that need expert handling 
5. Financial advice beyond basic information
6. Complaints, disputes, or sensitive customer service issues
7. Technical issues with the platform
8. Requests for actions the AI cannot perform

Assess both the user's query and the AI's response. Determine if escalation is needed and explain why.
"""
        }
        
        user_prompt = {
            "role": "user",
            "content": f"""Please evaluate this user query and AI response for escalation:

User query: {query}

AI response: {response}

Response confidence: {confidence:.2f}

Should this be escalated to a human operator? Return your analysis as JSON:
{{
    "needs_escalation": true/false,
    "reason": "Brief explanation of why escalation is needed or not needed"
}}
"""
        }
        
        try:
            # Call the LLM for escalation evaluation
            result = await self.llm_service.chat_completion(
                messages=[system_prompt, user_prompt],
                response_format={"type": "json_object"}
            )
            
            needs_escalation = result.get("needs_escalation", False)
            reason = result.get("reason", "")
            
            logger.info(f"Escalation evaluation: {needs_escalation}, reason: {reason}")
            
            return {
                "needs_escalation": needs_escalation,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error evaluating escalation: {str(e)}")
            # Default to escalation on error
            return {
                "needs_escalation": True,
                "reason": f"Error evaluating escalation: {str(e)}"
            }
    
    async def _handle_escalation(
        self, query: str, response: str, reason: str, user_id: str, session_id: str
    ) -> Dict[str, Any]:
        """
        Handle the escalation process.
        
        Args:
            query: User query
            response: AI-generated response
            reason: Reason for escalation
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Dict[str, Any]: Escalation result
        """
        # In a real system, this would:
        # 1. Create a ticket in a support system
        # 2. Notify available human operators
        # 3. Save the conversation context for the operator
        # 4. Generate an interim response for the user
        
        # Get conversation history for context
        conversation_history = await self.memory_service.get_conversation_memory(
            user_id=user_id,
            session_id=session_id,
            limit=10
        )
        
        # Format conversation history
        formatted_history = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'} ({msg.get('timestamp', 'Unknown time')}): {msg['content']}"
            for msg in conversation_history
        ])
        
        # Generate an interim response with LLM
        system_prompt = {
            "role": "system",
            "content": """You are the AI assistant for LenDen Club.
A user's query needs to be escalated to a human operator. 
Generate a polite, empathetic interim response that:
1. Acknowledges their question
2. Explains that a human team member will assist them
3. Sets appropriate expectations about response time
4. If possible, offers a partial answer or guidance while they wait

Be honest, helpful, and focus on ensuring a good customer experience during the handoff.
"""
        }
        
        user_prompt = {
            "role": "user",
            "content": f"""User query requiring escalation: {query}

Proposed AI response (may be insufficient): {response}

Escalation reason: {reason}

Generate an interim response that acknowledges the user's query, explains that it's been escalated to a human operator, and provides any helpful information while they wait.
"""
        }
        
        try:
            # Generate an interim response
            result = await self.llm_service.chat_completion(
                messages=[system_prompt, user_prompt]
            )
            
            interim_response = result
            
            # Create a dummy escalation ID - in a real system, this would be from the ticket system
            escalation_id = f"ESC-{hash(user_id + session_id + query) % 10000:04d}"
            
            # Save the escalation to memory for tracking
            await self.memory_service.add_system_message(
                user_id=user_id,
                session_id=session_id,
                content=f"Query escalated to human operator. Escalation ID: {escalation_id}",
                metadata={
                    "escalation_id": escalation_id,
                    "reason": reason,
                    "query": query,
                    "proposed_response": response,
                    "status": "pending"
                }
            )
            
            return {
                "escalation_id": escalation_id,
                "interim_response": interim_response,
                "estimated_wait_time": 15,  # Dummy value in minutes
                "status": "pending"
            }
            
        except Exception as e:
            logger.error(f"Error handling escalation: {str(e)}")
            
            # Fallback response
            default_response = "I'll need to connect you with a human specialist to better assist with your query. A team member will get back to you shortly. Thank you for your patience."
            
            return {
                "escalation_id": f"ESC-ERR-{hash(str(e)) % 10000:04d}",
                "interim_response": default_response,
                "estimated_wait_time": 30,  # Higher estimate on error
                "status": "error"
            }
    
    async def resolve_escalation(
        self, escalation_id: str, resolution: str, user_id: str, session_id: str
    ) -> Dict[str, Any]:
        """
        Resolve an escalated query with a human response.
        
        Args:
            escalation_id: ID of the escalation
            resolution: Human operator's resolution
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Dict[str, Any]: Resolution result
        """
        try:
            # Update the escalation status in memory
            await self.memory_service.add_system_message(
                user_id=user_id,
                session_id=session_id,
                content=f"Escalation {escalation_id} resolved by human operator",
                metadata={
                    "escalation_id": escalation_id,
                    "status": "resolved"
                }
            )
            
            # Add the human response as an assistant message
            await self.memory_service.add_assistant_message(
                user_id=user_id,
                session_id=session_id,
                content=resolution,
                metadata={
                    "source": "human_operator",
                    "escalation_id": escalation_id
                }
            )
            
            return {
                "status": "success",
                "escalation_id": escalation_id,
                "message": "Escalation resolved successfully"
            }
            
        except Exception as e:
            logger.error(f"Error resolving escalation: {str(e)}")
            return {
                "status": "error",
                "message": f"Error resolving escalation: {str(e)}",
                "escalation_id": escalation_id
            }
