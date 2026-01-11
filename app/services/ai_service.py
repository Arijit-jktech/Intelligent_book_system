import os
import logging
import httpx
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

# ============================================================================
# OLLAMA CONFIGURATION - All externalized to environment variables
# ============================================================================

# API Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3:8b")

# Request Configuration
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_RETRIES = int(os.getenv("OLLAMA_RETRIES", "3"))
OLLAMA_BACKOFF = float(os.getenv("OLLAMA_BACKOFF", "1"))

# Token and Generation Limits
# These prevent runaway tokens and excessive generation costs
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "512"))
OLLAMA_MIN_TOKENS = int(os.getenv("OLLAMA_MIN_TOKENS", "100"))
OLLAMA_MAX_CONTEXT = int(os.getenv("OLLAMA_MAX_CONTEXT", "4096"))

# Model Behavior Configuration
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))  # 0=deterministic, 1=creative
OLLAMA_TOP_P = float(os.getenv("OLLAMA_TOP_P", "0.9"))  # nucleus sampling
OLLAMA_TOP_K = int(os.getenv("OLLAMA_TOP_K", "40"))  # top-k sampling
OLLAMA_REPEAT_PENALTY = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.1"))

logger.info(
    "Ollama configured: URL=%s, Model=%s, MaxTokens=%s, Timeout=%s",
    OLLAMA_URL, MODEL_NAME, OLLAMA_MAX_TOKENS, OLLAMA_TIMEOUT
)


# ============================================================================
# TOKEN AND CONTEXT MANAGEMENT
# ============================================================================

def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count.
    Most LLMs use approximately 1 token per 4 characters.
    This is a conservative estimate for planning purposes.
    """
    return len(text) // 4


def validate_context_length(prompt: str, margin: int = 100) -> bool:
    """
    Validate that prompt won't exceed model context window.
    margin: safety margin (tokens) to reserve for response
    """
    prompt_tokens = estimate_tokens(prompt)
    required_tokens = prompt_tokens + margin
    
    if required_tokens > OLLAMA_MAX_CONTEXT:
        logger.warning(
            "Prompt exceeds context window: %d tokens required, %d available (margin: %d)",
            prompt_tokens, OLLAMA_MAX_CONTEXT, margin
        )
        return False
    
    logger.debug(
        "Prompt token estimate: %d (max: %d, margin: %d)",
        prompt_tokens, OLLAMA_MAX_CONTEXT, margin
    )
    return True


def truncate_to_context(text: str, max_tokens: int) -> str:
    """Truncate text to fit within token limit."""
    max_chars = max_tokens * 4  # rough estimate
    if len(text) <= max_chars:
        return text
    
    truncated = text[:max_chars]
    logger.warning("Truncated text from %d to %d chars to fit context", len(text), len(truncated))
    return truncated


# ============================================================================
# OLLAMA PAYLOAD BUILDERS
# ============================================================================

def build_ollama_payload(
    prompt: str,
    num_predict: Optional[int] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build a standardized Ollama API payload with model configuration.
    
    Args:
        prompt: The input prompt
        num_predict: Max tokens to generate (overrides OLLAMA_MAX_TOKENS)
        temperature: Generation temperature (overrides OLLAMA_TEMPERATURE)
        top_p: Nucleus sampling (overrides OLLAMA_TOP_P)
        top_k: Top-k sampling (overrides OLLAMA_TOP_K)
    
    Returns:
        Dictionary ready for Ollama API
    """
    return {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        # Generation parameters with configured defaults
        "options": {
            "num_predict": num_predict or OLLAMA_MAX_TOKENS,
            "temperature": temperature or OLLAMA_TEMPERATURE,
            "top_p": top_p or OLLAMA_TOP_P,
            "top_k": top_k or OLLAMA_TOP_K,
            "repeat_penalty": OLLAMA_REPEAT_PENALTY,
        }
    }


def _fallback_book_summary(book_data: dict) -> str:
    # Simple non-AI fallback summary
    title = book_data.get("title", "Unknown title")
    author = book_data.get("author", "Unknown author")
    genre = book_data.get("genre")
    year = book_data.get("year_published")
    parts = [f"{title} by {author}"]
    if genre:
        parts.append(f"Genre: {genre}")
    if year:
        parts.append(f"Year: {year}")
    parts.append("(AI summary unavailable — showing basic metadata)")
    return " — ".join(parts)


def _fallback_review_summary(reviews: List[str]) -> str:
    if not reviews:
        return "No reviews available."
    # Return a short concatenation of first few reviews as a fallback
    sample = " \n\n ".join(reviews[:3])
    if len(sample) > 500:
        sample = sample[:497] + "..."
    return f"Fallback summary (first reviews): {sample}"


async def _call_ollama(payload: dict) -> dict:
    """
    Call Ollama with retries and exponential backoff. 
    Returns parsed JSON or a dict with an "error" key.
    
    Args:
        payload: Dictionary containing model, prompt, options, etc.
    
    Returns:
        Response dict with 'response' key or 'error' key
    """
    attempt = 0
    last_exc = None
    
    while attempt < OLLAMA_RETRIES:
        attempt += 1
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            try:
                logger.debug(
                    "Ollama request attempt %s to %s (model=%s, tokens=%s)",
                    attempt, OLLAMA_URL, MODEL_NAME,
                    payload.get("options", {}).get("num_predict", "?")
                )
                resp = await client.post(OLLAMA_URL, json=payload)
            except httpx.ReadTimeout as exc:
                logger.warning("Ollama read timeout on attempt %s: %r", attempt, exc)
                last_exc = exc
                resp = None
            except httpx.RequestError as exc:
                logger.error("Ollama request to %s failed on attempt %s: %r", OLLAMA_URL, attempt, exc)
                last_exc = exc
                resp = None

        if resp is None:
            if attempt < OLLAMA_RETRIES:
                backoff = OLLAMA_BACKOFF * (2 ** (attempt - 1))
                logger.info(
                    "Retrying Ollama request in %.1fs (attempt %s/%s)",
                    backoff, attempt + 1, OLLAMA_RETRIES
                )
                await __import__("asyncio").sleep(backoff)
                continue
            else:
                return {
                    "error": f"request_error: {repr(last_exc)}",
                    "url": OLLAMA_URL,
                    "model": MODEL_NAME
                }

        # Non-2xx responses should be surfaced with body if available
        if resp.status_code < 200 or resp.status_code >= 300:
            try:
                body = resp.json()
            except Exception:
                try:
                    raw = resp.text
                except Exception:
                    raw = f"(unable to read body, status {resp.status_code})"
                body = raw
            logger.error("Ollama returned HTTP %s for %s: %s", resp.status_code, OLLAMA_URL, body)
            return {
                "error": f"http_error {resp.status_code}: {body}",
                "url": OLLAMA_URL,
                "model": MODEL_NAME
            }

        # Parse JSON response
        try:
            result = resp.json()
            # Log token usage if available
            if "prompt_eval_count" in result:
                logger.debug(
                    "Ollama response: prompt_tokens=%s, completion_tokens=%s",
                    result.get("prompt_eval_count"),
                    result.get("eval_count")
                )
            return result
        except Exception:
            logger.error(
                "Invalid JSON response from Ollama at %s (status %s)",
                OLLAMA_URL, resp.status_code
            )
            return {
                "error": f"invalid_json_response (status {resp.status_code})",
                "url": OLLAMA_URL,
                "model": MODEL_NAME
            }


async def generate_book_summary(book_data: dict) -> str:
    """
    Generate a book summary using Ollama with token limits and context validation.
    Falls back to metadata summary if AI is unavailable.
    
    Args:
        book_data: Dictionary with 'title', 'author', 'genre', 'year_published'
    
    Returns:
        Summary string (AI-generated or fallback)
    """
    prompt = f"""Generate a concise and professional summary for the following book.

Title: {book_data.get('title')}
Author: {book_data.get('author')}
Genre: {book_data.get('genre')}
Year: {book_data.get('year_published')}

Summary (max 200 words):"""

    # Validate context window before calling Ollama
    if not validate_context_length(prompt, margin=OLLAMA_MAX_TOKENS):
        logger.warning("Book summary prompt exceeds context window, using fallback")
        return _fallback_book_summary(book_data)

    # Build payload with token limits
    payload = build_ollama_payload(
        prompt=prompt,
        num_predict=256,  # ~200 words
        temperature=0.7  # Balanced between creativity and consistency
    )

    try:
        result = await _call_ollama(payload)
    except Exception as exc:
        logger.error("Ollama request failed with exception: %s", exc)
        return _fallback_book_summary(book_data)

    # Handle Ollama errors
    if not isinstance(result, dict):
        logger.error("Ollama returned unexpected non-dict response")
        return _fallback_book_summary(book_data)
    
    if result.get("error"):
        logger.error("Ollama returned error: %s", result.get("error"))
        return _fallback_book_summary(book_data)

    # Extract response
    ai_text = result.get("response") or result.get("text") or ""
    if not ai_text or len(ai_text.strip()) < OLLAMA_MIN_TOKENS // 4:
        logger.warning("Ollama returned empty or too-short response")
        return _fallback_book_summary(book_data)
    
    logger.info("Generated book summary (%d chars)", len(ai_text))
    return ai_text


async def generate_review_summary(reviews: List[str]) -> str:
    """
    Generate a review summary using Ollama with token limits.
    Falls back to first few reviews if AI is unavailable.
    
    Args:
        reviews: List of review text strings
    
    Returns:
        Summary string (AI-generated or fallback)
    """
    # Limit reviews to prevent excessive context usage
    max_reviews = 5
    selected_reviews = reviews[:max_reviews]
    
    joined_reviews = "\n---\n".join(selected_reviews)
    
    # Truncate reviews if they exceed context limit
    joined_reviews = truncate_to_context(joined_reviews, OLLAMA_MAX_CONTEXT - OLLAMA_MAX_TOKENS - 200)
    
    prompt = f"""Analyze and summarize the following book reviews. Provide:
1. Overall sentiment (positive/negative/neutral)
2. Key positive points
3. Key criticisms
4. Overall recommendation (0-10)

Reviews:
{joined_reviews}

Summary:"""

    # Validate context
    if not validate_context_length(prompt, margin=OLLAMA_MAX_TOKENS):
        logger.warning("Review summary prompt exceeds context window, using fallback")
        return _fallback_review_summary(reviews)

    # Build payload with token limits
    payload = build_ollama_payload(
        prompt=prompt,
        num_predict=512,  # Allow more tokens for structured analysis
        temperature=0.5  # Lower temperature for more consistent analysis
    )

    try:
        result = await _call_ollama(payload)
    except Exception as exc:
        logger.error("Ollama request failed with exception: %s", exc)
        return _fallback_review_summary(reviews)

    if not isinstance(result, dict):
        logger.error("Ollama returned unexpected non-dict response for reviews")
        return _fallback_review_summary(reviews)
    
    if result.get("error"):
        logger.error("Ollama returned error for reviews: %s", result.get("error"))
        return _fallback_review_summary(reviews)

    ai_text = result.get("response") or result.get("text") or ""
    if not ai_text or len(ai_text.strip()) < OLLAMA_MIN_TOKENS // 4:
        logger.warning("Ollama returned empty or too-short review summary")
        return _fallback_review_summary(reviews)
    
    logger.info("Generated review summary (%d chars)", len(ai_text))
    return ai_text
