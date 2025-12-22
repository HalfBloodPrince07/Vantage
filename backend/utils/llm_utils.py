# backend/utils/llm_utils.py
"""
Centralized LLM Utilities with Retry Logic and Fail-Safes

Provides robust wrapper functions for all LLM calls with:
- Automatic retry logic
- Response validation
- Comprehensive error handling
- Fallback mechanisms
"""

import httpx
import json
from typing import Dict, Any, Optional, Callable, List
from loguru import logger
import asyncio
from backend.utils.model_manager import get_model_manager


class LLMCallError(Exception):
    """Custom exception for LLM call failures"""
    pass


async def call_ollama_with_retry(
    base_url: str,
    model: str,
    prompt: str,
    max_retries: int = 3,
    timeout: float = 30.0,
    temperature: float = 0.3,
    format: Optional[str] = None,
    stream: bool = False,
    fallback_response: Optional[str] = None,
    validator: Optional[Callable[[str], bool]] = None,
    model_type: str = "text",
    images: Optional[List[str]] = None,
    config: Optional[Dict] = None,
    think: bool = False  # Enable Ollama thinking mode for chain-of-thought reasoning
) -> str:
    """
    Call Ollama API with automatic retry and validation
    
    Args:
        base_url: Ollama base URL
        model: Model name
        prompt: Input prompt
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        temperature: LLM temperature
        format: Response format ("json" or None)
        stream: Whether to stream response
        fallback_response: Fallback response if all retries fail
        validator: Optional function to validate response
        model_type: Type of model ("text" or "vision")
        images: List of base64-encoded images for vision models
        config: Full config dict for model manager
        
    Returns:
        LLM response text
        
    Raises:
        LLMCallError: If all retries fail and no fallback is provided
    """
    # Ensure model is loaded if config provided
    if config:
        try:
            model_manager = get_model_manager(base_url, config)
            await model_manager.ensure_model_loaded(model, model_type)
        except Exception as e:
            logger.warning(f"Model manager failed: {e}, proceeding without it")
    last_error = None
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                request_data = {
                    "model": model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": {"temperature": temperature},
                    "think": think  # Enable chain-of-thought reasoning
                }
                
                # Add images for vision models
                if images and model_type == "vision":
                    request_data["images"] = images
                
                if format:
                    request_data["format"] = format
                
                if think:
                    logger.debug(f"🧠 Thinking mode enabled for this LLM call")
                
                logger.debug(f"LLM call attempt {attempt + 1}/{max_retries}")
                
                response = await client.post(
                    f"{base_url}/api/generate",
                    json=request_data
                )
                response.raise_for_status()
                
                result = response.json()
                response_text = result.get('response', '').strip()
                
                # Extract thinking content if present (from Ollama's thinking mode)
                thinking_content = result.get('thinking', '')
                if thinking_content:
                    logger.debug(f"🧠 LLM thinking captured ({len(thinking_content)} chars)")
                
                # Validate response is not empty
                if not response_text:
                    logger.warning(f"Empty LLM response on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        raise LLMCallError("LLM returned empty response after all retries")
                
                # Run custom validator if provided
                if validator and not validator(response_text):
                    logger.warning(f"Response failed validation on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    else:
                        raise LLMCallError("Response failed validation after all retries")
                
                logger.debug(f"LLM call successful on attempt {attempt + 1}")
                return response_text
                
        except httpx.TimeoutException as e:
            last_error = e
            logger.warning(f"LLM request timeout on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))
                
        except httpx.HTTPStatusError as e:
            last_error = e
            logger.error(f"LLM HTTP error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))
                
        except Exception as e:
            last_error = e
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0 * (attempt + 1))
    
    # All retries failed
    if fallback_response:
        logger.warning(f"All LLM retries failed, using fallback response. Last error: {last_error}")
        return fallback_response
    else:
        raise LLMCallError(f"LLM call failed after {max_retries} retries: {last_error}")


async def call_ollama_json(
    base_url: str,
    model: str,
    prompt: str,
    max_retries: int = 3,
    timeout: float = 30.0,
    temperature: float = 0.2,
    fallback_data: Optional[Dict] = None,
    model_type: str = "text",
    config: Optional[Dict] = None,
    think: bool = False  # Enable Ollama thinking mode
) -> Dict[str, Any]:
    """
    Call Ollama API expecting JSON response
    
    Args:
        base_url: Ollama base URL
        model: Model name
        prompt: Input prompt
        max_retries: Maximum retries
        timeout: Request timeout
        temperature: LLM temperature
        fallback_data: Fallback dict if parsing fails
        model_type: Type of model ("text" or "vision")
        config: Full config dict for model manager
        think: Enable chain-of-thought reasoning
        
    Returns:
        Parsed JSON dict
    """
    def validate_json(text: str) -> bool:
        """Validate that text is valid JSON"""
        try:
            # Sanitize before validation to handle markdown code blocks
            cleaned = sanitize_llm_response(text)
            json.loads(cleaned)
            return True
        except json.JSONDecodeError:
            return False
    
    # Qwen3-VL (and potentially other VL models) fails when format="json" is enforced
    # So we disable it for Qwen models and rely on the prompt and parsing
    use_json_format = "json"
    if "qwen" in model.lower() or "vl" in model.lower():
        use_json_format = None
        
    try:
        response_text = await call_ollama_with_retry(
            base_url=base_url,
            model=model,
            prompt=prompt,
            max_retries=max_retries,
            timeout=timeout,
            temperature=temperature,
            format=use_json_format,
            validator=validate_json,
            fallback_response=None,  # We'll handle fallback after JSON parsing
            model_type=model_type,
            config=config,
            think=think  # Pass through thinking mode
        )
        
        # Parse JSON
        try:
            # Sanitize response first (remove markdown blocks if any)
            cleaned_text = sanitize_llm_response(response_text)
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            if fallback_data:
                logger.warning("Using fallback data for JSON response")
                return fallback_data
            else:
                raise LLMCallError(f"Invalid JSON response: {e}")
                
    except LLMCallError as e:
        if fallback_data:
            logger.warning(f"LLM call failed, using fallback data: {e}")
            return fallback_data
        else:
            raise


def validate_document_content(document: Dict[str, Any]) -> bool:
    """
    Validate that a document has usable content
    
    Args:
        document: Document dict
        
    Returns:
        True if document has content, False otherwise
    """
    # Check for content_summary first
    content_summary = document.get('content_summary', '').strip()
    if content_summary and len(content_summary) > 10:
        return True
    
    # Check for raw content
    content = document.get('content', '').strip()
    if content and len(content) > 10:
        return True
    
    # Check for text field (alternative)
    text = document.get('text', '').strip()
    if text and len(text) > 10:
        return True
    
    return False


def get_document_content(document: Dict[str, Any], max_length: int = 1000) -> str:
    """
    Extract content from document in priority order
    
    Args:
        document: Document dict
        max_length: Maximum content length
        
    Returns:
        Document content string
    """
    # Priority order: content_summary > content > text > filename
    content = (
        document.get('content_summary', '') or
        document.get('content', '') or
        document.get('text', '') or
        f"Document: {document.get('filename', 'unknown')}"
    )
    
    return content.strip()[:max_length]


def sanitize_llm_response(response: str) -> str:
    """
    Sanitize LLM response by extracting JSON from potentially messy output.
    
    Handles cases where LLM returns:
    - Pure JSON
    - JSON wrapped in markdown code blocks
    - JSON with text before/after it
    - Multiple JSON objects (takes the first one)
    
    Args:
        response: Raw LLM response
        
    Returns:
        Cleaned JSON string
    """
    import re
    
    if not response:
        return "{}"
    
    text = response.strip()
    
    # Step 1: Remove markdown code blocks
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    # Step 2: If it's already valid JSON, return it
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    
    # Step 3: Try to extract JSON object from text
    # Look for { ... } pattern
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        extracted = json_match.group(0)
        try:
            json.loads(extracted)
            return extracted
        except json.JSONDecodeError:
            pass
    
    # Step 4: Try more aggressive extraction - find first { and last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    
    # Step 5: Return original (let caller handle the error)
    return text.strip()

