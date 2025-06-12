"""
URL Scraper Agent - Extract content from URLs.

This agent handles scraping content from web URLs,
processes the extracted content, and prepares it for storage.
"""
import logging
import aiohttp
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from typing import Dict, Any, List, Optional

from .base import Agent
from services.llm import LLMService

logger = logging.getLogger(__name__)

class URLScraperAgent(Agent):
    """
    Agent for scraping and processing web content.
    
    This agent extracts text content from URLs, processes it,
    and prepares it for storage in the knowledge base.
    """
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize the URL scraper agent.
        
        Args:
            llm_service: Service for language model processing
        """
        super().__init__()
        self.llm_service = llm_service
        self.session = None
    
    async def _get_session(self):
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "Mozilla/5.0 LenDen Club AI Agent"}
            )
        return self.session
    
    async def process(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a URL scraping request.
        
        Args:
            input_data: Input data containing URL information
            context: Additional context
            
        Returns:
            Dict[str, Any]: Processing result with extracted content
        """
        url = input_data.get("url")
        if not url:
            logger.error("No URL provided")
            return {
                "status": "error",
                "message": "No URL provided"
            }
        
        try:
            # Scrape content from URL
            content = await self._scrape_url(url)
            if not content:
                return {
                    "status": "error",
                    "message": f"Failed to extract content from URL: {url}"
                }
            
            # Analyze and summarize content
            content_summary = await self._analyze_content(content, url)
            
            return {
                "status": "success",
                "message": "URL content extracted successfully",
                "url": url,
                "content": content[:500] + "..." if len(content) > 500 else content,  # Truncate for response
                "title": content_summary.get("title", ""),
                "summary": content_summary.get("summary", ""),
                "metadata": {
                    "source_url": url,
                    "key_points": content_summary.get("key_points", []),
                    "categories": content_summary.get("categories", []),
                    "content_length": len(content),
                    "scraped_at": context.get("timestamp", ""),
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing URL: {str(e)}",
                "url": url
            }
    
    async def _scrape_url(self, url: str) -> Optional[str]:
        """
        Scrape content from a URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Optional[str]: Extracted content or None if extraction failed
        """
        try:
            session = await self._get_session()
            
            async with session.get(url, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"Error fetching URL {url}: HTTP {response.status}")
                    return None
                
                html = await response.text()
                
                # Parse HTML
                soup = BeautifulSoup(html, "html.parser")
                
                # Remove script, style, and other non-content elements
                for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    element.extract()
                
                # Extract main content (focusing on article, main, or content div if present)
                main_content = None
                for tag in ["article", "main", "div.content", "div.main", "#content", "#main"]:
                    main_content = soup.select_one(tag)
                    if main_content:
                        break
                
                if not main_content:
                    # If no main content container found, use the whole body
                    main_content = soup.body
                
                if not main_content:
                    # If body not found, use the whole document
                    main_content = soup
                
                # Convert to markdown for clean text representation
                markdown = md(str(main_content))
                
                return markdown
                
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return None
    
    async def _analyze_content(self, content: str, url: str) -> Dict[str, Any]:
        """
        Analyze scraped content using LLM to extract metadata.
        
        Args:
            content: Scraped content
            url: Source URL
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        # Truncate content if too large
        truncated_content = content[:5000] + "..." if len(content) > 5000 else content
        
        analysis_prompt = {
            "role": "system",
            "content": f"""Analyze the following web content scraped from URL: {url}

Extract the following information:
1. A suitable title for this content (if not clear from the content)
2. A brief summary (3-4 sentences)
3. 3-5 key points or facts from the content
4. 5-8 suggested categories or tags that describe the content

Return your analysis as a JSON object with the following structure:
{{
    "title": "Extracted or inferred title",
    "summary": "Brief summary of the content",
    "key_points": ["Key point 1", "Key point 2", ...],
    "categories": ["category1", "category2", ...]
}}
"""
        }
        
        try:
            result = await self.llm_service.chat_completion(
                messages=[
                    analysis_prompt,
                    {"role": "user", "content": truncated_content}
                ],
                response_format={"type": "json_object"}
            )
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing content: {str(e)}")
            return {
                "title": url.split("/")[-1].replace("-", " ").replace("_", " ").title(),
                "summary": "Error analyzing content",
                "key_points": [],
                "categories": []
            }
    
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("Closed URL scraper session")
