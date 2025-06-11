from typing import Dict, Any, List
import asyncio
from .file_processing_agent import FileProcessingAgent
from .query_processing_agent import QueryProcessingAgent
from .response_synthesis_agent import ResponseSynthesisAgent
from .web_search_agent import WebSearchAgent
from .email_agent import EmailAgent

class MainAgent:
    def __init__(self):
        self.file_processor = FileProcessingAgent()
        self.query_processor = QueryProcessingAgent()
        self.response_synthesizer = ResponseSynthesisAgent()
        self.web_searcher = WebSearchAgent()
        self.email_agent = EmailAgent()

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Main orchestration method for all requests"""
        try:
            request_type = request.get('type')

            if request_type == 'file_upload':
                return await self._handle_file_upload(request)
            elif request_type == 'user_query':
                return await self._handle_user_query(request)
            else:
                return {"error": "Unknown request type"}

        except Exception as e:
            return {"error": f"Processing failed: {str(e)}"}

    async def _handle_file_upload(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin file uploads"""
        file_data = request.get('file_data')
        file_type = request.get('file_type')
        category = request.get('category', 'general')

        result = await self.file_processor.process_file(
            file_data=file_data,
            file_type=file_type,
            category=category
        )

        return {
            "status": "success" if result.get("processed") else "failed",
            "message": result.get("message"),
            "document_id": result.get("document_id")
        }

    async def _handle_user_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user queries with multi-intent support"""
        user_id = request.get('user_id')
        session_id = request.get('session_id')
        query = request.get('query')

        # Process query to identify intents
        analysis = await self.query_processor.analyze_query(query)

        # Route to appropriate agents based on intents
        agent_responses = []
        for intent in analysis.get('intents', []):
            response = await self._route_to_specialist_agent(intent, query, user_id)
            if response:
                agent_responses.append(response)

        # If no relevant responses, try web search
        if not agent_responses:
            web_result = await self.web_searcher.search(query)
            if web_result.get('relevant'):
                agent_responses.append(web_result)

        # If still no good response, escalate to email
        if not agent_responses:
            await self.email_agent.escalate_query(user_id, query)
            return {
                "response": "I've forwarded your query to our support team. You'll receive an email response shortly.",
                "escalated": True
            }

        # Synthesize responses
        final_response = await self.response_synthesizer.combine_responses(
            responses=agent_responses,
            original_query=query,
            user_context={"user_id": user_id, "session_id": session_id}
        )

        return {
            "response": final_response,
            "agents_used": [r.get('agent_type') for r in agent_responses]
        }

    async def _route_to_specialist_agent(self, intent: str, query: str, user_id: str):
        """Route to appropriate specialist agent"""
        # Import agents dynamically to avoid circular imports
        from .loan_agent import LoanAgent
        from .account_agent import AccountAgent
        from .policy_agent import PolicyAgent

        agent_map = {
            'loan_inquiry': LoanAgent(),
            'account_management': AccountAgent(),
            'policy_question': PolicyAgent()
        }

        agent = agent_map.get(intent)
        if agent:
            return await agent.process_query(query, user_id)

        return None
