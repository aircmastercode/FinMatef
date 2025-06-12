"""
Response Combiner Agent - Synthesize responses from multiple sources.

This agent combines responses from multiple specialist agents
and generates a unified, coherent response for the user.
"""
import logging
import json
from typing import Dict, Any, List, Optional

from .base import Agent
from services.llm import LLMService

logger = logging.getLogger(__name__)

class ResponseCombinerAgent(Agent):
    """
    Agent for combining responses from multiple sources.
    
    This agent takes multiple responses from specialist agents,
    synthesizes the information, removes redundancies,
    and generates a unified, coherent response.
    """
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize the response combiner agent.
        
        Args:
            llm_service: Service for language model processing
        """
        super().__init__()
        self.llm_service = llm_service
    
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process multiple responses and combine them.
        
        Args:
            input_data: Input data containing multiple agent responses
            context: Additional context
            
        Returns:
            Dict[str, Any]: Combined response
        """
        responses = input_data.get("responses", [])
        original_query = input_data.get("original_query", "")
        
        if not responses:
            logger.error("No responses provided to combine")
            return {
                "status": "error",
                "message": "No responses provided to combine"
            }
        
        try:
            # Process and combine the responses
            combined_response = await self._combine_responses(responses, original_query)
            
            return {
                "status": "success",
                "message": "Responses combined successfully",
                "combined_response": combined_response["response"],
                "sources": combined_response["sources"],
                "confidence": combined_response["confidence"],
                "needs_escalation": combined_response["needs_escalation"],
                "escalation_reason": combined_response.get("escalation_reason", "")
            }
            
        except Exception as e:
            logger.error(f"Error combining responses: {str(e)}")
            return {
                "status": "error",
                "message": f"Error combining responses: {str(e)}"
            }
    
    async def _combine_responses(self, responses: List[Dict[str, Any]], original_query: str) -> Dict[str, Any]:
        """
        Combine multiple responses into a unified response.
        
        Args:
            responses: List of response objects from different agents
            original_query: The original user query
            
        Returns:
            Dict[str, Any]: Combined response
        """
        # Extract responses and metadata
        response_texts = []
        all_sources = []
        max_confidence = 0.0
        needs_escalation = False
        escalation_reasons = []
        
        for response in responses:
            # Get the response text
            response_text = response.get("response", "")
            if response_text:
                response_texts.append(response_text)
            
            # Collect sources
            sources = response.get("sources", [])
            if sources:
                all_sources.extend(sources)
            
            # Track confidence
            confidence = float(response.get("confidence", 0.0))
            max_confidence = max(max_confidence, confidence)
            
            # Check for escalation needs
            if response.get("needs_escalation", False):
                needs_escalation = True
                reason = response.get("escalation_reason")
                if reason:
                    escalation_reasons.append(reason)
        
        # Deduplicate sources
        unique_sources = list(dict.fromkeys(all_sources))
        
        # If no responses, return error
        if not response_texts:
            return {
                "response": "I don't have enough information to provide a response at this time.",
                "sources": [],
                "confidence": 0.0,
                "needs_escalation": True,
                "escalation_reason": "No valid responses received from specialist agents."
            }
        
        # If only one response, return it directly
        if len(response_texts) == 1:
            return {
                "response": response_texts[0],
                "sources": unique_sources,
                "confidence": max_confidence,
                "needs_escalation": needs_escalation,
                "escalation_reason": "; ".join(escalation_reasons) if escalation_reasons else ""
            }
        
        # For multiple responses, synthesize them
        responses_context = "\n\n".join([
            f"Response {i+1}:\n{response}" for i, response in enumerate(response_texts)
        ])
        
        system_prompt = {
            "role": "system",
            "content": """You are a response synthesizer for LenDen Club's AI assistant.
Your task is to combine multiple response fragments into a single, coherent, and comprehensive response.

When combining responses:
1. Synthesize information from all responses without redundancy
2. Maintain a consistent, helpful tone
3. Organize information logically
4. Preserve all factual information and important details
5. If responses contradict each other, acknowledge the contradiction and provide the most reliable information
6. Include appropriate citations to sources when relevant
7. Ensure the response directly answers the original query

Be concise yet complete in your synthesis.
"""
        }
        
        user_prompt = {
            "role": "user",
            "content": f"""Original user query: {original_query}

The following are multiple response fragments that need to be combined:

{responses_context}

Please synthesize these into a single, coherent response that addresses the original query.
For your internal assessment only (will not be shown to the user), include:
1. Confidence level (0-1) in your response
2. Whether this query needs human escalation (true/false)
3. Reason for escalation, if needed
"""
        }
        
        try:
            # Call the LLM for response synthesis
            completion_result = await self.llm_service.chat_completion(
                messages=[system_prompt, user_prompt],
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            synthesized_response = completion_result.get("response", "")
            confidence = float(completion_result.get("confidence", max_confidence))
            needs_escalation = completion_result.get("needs_escalation", needs_escalation)
            escalation_reason = completion_result.get("escalation_reason", "; ".join(escalation_reasons))
            
            return {
                "response": synthesized_response,
                "sources": unique_sources,
                "confidence": confidence,
                "needs_escalation": needs_escalation,
                "escalation_reason": escalation_reason
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing responses: {str(e)}")
            
            # Fallback: concatenate responses
            fallback_response = "\n\n".join([
                f"{response}" for response in response_texts
            ])
            
            return {
                "response": fallback_response,
                "sources": unique_sources,
                "confidence": max_confidence * 0.8,  # Lower confidence due to fallback
                "needs_escalation": True,
                "escalation_reason": f"Error synthesizing responses: {str(e)}"
            }
