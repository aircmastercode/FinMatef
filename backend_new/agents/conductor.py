"""
Conductor Agent - Main orchestration agent for the system.

The conductor agent analyzes queries, determines intent, and delegates tasks
to the appropriate specialist agents.
"""
from typing import Dict, Any, List
import logging
from .base import Agent
from services.llm import LLMService

logger = logging.getLogger(__name__)

class ConductorAgent(Agent):
    """
    Main orchestration agent that delegates tasks to specialist agents.
    
    This agent is responsible for:
    1. Analyzing user queries to determine intent
    2. Routing queries to appropriate specialist agents
    3. Handling multi-intent queries by coordinating multiple agents
    4. Collecting and combining responses
    """
    
    def __init__(self, agents: Dict[str, Agent], llm_service: LLMService):
        """
        Initialize the conductor agent with specialist agents and LLM service.
        
        Args:
            agents: Dictionary mapping agent names to agent instances
            llm_service: LLM service for intent analysis
        """
        super().__init__()
        self.agents = agents
        self.llm_service = llm_service
    
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user query by delegating to appropriate specialist agents.
        
        Args:
            input_data: The input data including the user query
            context: Additional context information including user history
            
        Returns:
            Dict[str, Any]: The processed result
        """
        query = input_data.get("query", "")
        logger.info(f"Conductor processing query: {query[:100]}...")
        
        # Analyze intent
        intent_analysis = await self.analyze_intent(query, context)
        
        if intent_analysis.get("is_multi_intent", False):
            logger.info(f"Detected multi-intent query with {len(intent_analysis.get('intents', []))} intents")
            return await self._handle_multi_intent_query(input_data, intent_analysis, context)
        else:
            logger.info(f"Detected single intent: {intent_analysis.get('intent', 'unknown')}")
            return await self._handle_single_intent_query(input_data, intent_analysis, context)
    
    async def analyze_intent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a query to determine intent and complexity.
        
        Args:
            query: The user query
            context: Additional context information
            
        Returns:
            Dict[str, Any]: Analysis results including intent information
        """
        # Use LLM to analyze the query for intent
        analysis_prompt = {
            "role": "system",
            "content": """Analyze the user query and determine:
1. The primary intent of the query
2. Whether the query contains multiple intents
3. If multiple intents are present, list each intent separately
4. Which agent would be best suited to handle each intent

Return your analysis as a JSON object with the following structure:
{
    "is_multi_intent": boolean,
    "intent": "primary intent category",
    "intents": [list of intent categories if multi-intent],
    "agent_mapping": {"intent": "agent_type"}
}

Available agent types:
- query_handler: For simple information retrieval
- web_search: For information that might require searching the web
- escalation: For queries requiring human assistance
"""
        }
        
        result = await self.llm_service.chat_completion(
            messages=[
                analysis_prompt,
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        return result
    
    async def _handle_single_intent_query(
        self, input_data: Dict[str, Any], intent_analysis: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle a query with a single intent.
        
        Args:
            input_data: The input data including the user query
            intent_analysis: The intent analysis results
            context: Additional context information
            
        Returns:
            Dict[str, Any]: The processed result
        """
        intent = intent_analysis.get("intent", "query_handler")
        agent_name = self._get_agent_for_intent(intent)
        
        if agent_name not in self.agents:
            logger.warning(f"No agent found for intent {intent}, falling back to query_handler")
            agent_name = "query_handler"
        
        agent = self.agents[agent_name]
        logger.info(f"Delegating to {agent_name} agent")
        
        # Add intent analysis to the input
        input_with_intent = input_data.copy()
        input_with_intent["intent"] = intent
        input_with_intent["intent_analysis"] = intent_analysis
        
        return await agent.run(input_with_intent, context)
    
    async def _handle_multi_intent_query(
        self, input_data: Dict[str, Any], intent_analysis: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle a query with multiple intents.
        
        Args:
            input_data: The input data including the user query
            intent_analysis: The intent analysis results
            context: Additional context information
            
        Returns:
            Dict[str, Any]: The processed result
        """
        # Step 1: Use multi_intent agent to break down the query
        multi_intent_agent = self.agents["multi_intent"]
        multi_intent_input = input_data.copy()
        multi_intent_input["intent_analysis"] = intent_analysis
        
        breakdown_result = await multi_intent_agent.run(multi_intent_input, context)
        sub_queries = breakdown_result.get("sub_queries", [])
        
        if not sub_queries:
            logger.warning("Multi-intent agent returned no sub-queries, falling back to query_handler")
            return await self._handle_single_intent_query(input_data, {"intent": "query_handler"}, context)
        
        # Step 2: Process each sub-query with the appropriate agent
        sub_results = []
        for sub_query in sub_queries:
            sub_input = input_data.copy()
            sub_input["query"] = sub_query["text"]
            sub_input["intent"] = sub_query["intent"]
            
            agent_name = self._get_agent_for_intent(sub_query["intent"])
            if agent_name not in self.agents:
                logger.warning(f"No agent found for intent {sub_query['intent']}, falling back to query_handler")
                agent_name = "query_handler"
            
            agent = self.agents[agent_name]
            logger.info(f"Delegating sub-query to {agent_name} agent")
            
            try:
                sub_result = await agent.run(sub_input, context)
                sub_results.append({
                    "query": sub_query["text"],
                    "intent": sub_query["intent"],
                    "result": sub_result
                })
            except Exception as e:
                logger.error(f"Error processing sub-query with {agent_name} agent: {str(e)}")
                sub_results.append({
                    "query": sub_query["text"],
                    "intent": sub_query["intent"],
                    "result": {"status": "error", "message": str(e)}
                })
        
        # Step 3: Combine the results using response_combiner agent
        response_combiner = self.agents["response_combiner"]
        combiner_input = {
            "original_query": input_data["query"],
            "sub_results": sub_results
        }
        
        return await response_combiner.run(combiner_input, context)
    
    def _get_agent_for_intent(self, intent: str) -> str:
        """
        Map an intent to the appropriate agent name.
        
        Args:
            intent: The intent to map
            
        Returns:
            str: The name of the agent to handle the intent
        """
        intent_mapping = {
            "knowledge_query": "query_handler",
            "web_search": "web_search",
            "escalate": "escalation",
            "data_ingestion": "data_ingestion",
            "url_scraping": "url_scraper"
        }
        
        return intent_mapping.get(intent, "query_handler") 