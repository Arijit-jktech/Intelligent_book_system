import os
import logging
import httpx
from typing import List

logger = logging.getLogger(__name__)

# Configurable via environment variables
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3:8b")
# Timeout (seconds) and retry settings for Ollama requests
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_RETRIES = int(os.getenv("OLLAMA_RETRIES", "3"))
OLLAMA_BACKOFF = float(os.getenv("OLLAMA_BACKOFF", "1"))


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
    """Call Ollama with retries and exponential backoff. Returns parsed JSON or a dict with an "error" key."""
    attempt = 0
    last_exc = None
    while attempt < OLLAMA_RETRIES:
        attempt += 1
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            try:
                logger.debug("Ollama request attempt %s to %s (model=%s)", attempt, OLLAMA_URL, MODEL_NAME)
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
                logger.info("Retrying Ollama request in %.1fs (attempt %s/%s)", backoff, attempt + 1, OLLAMA_RETRIES)
                await __import__("asyncio").sleep(backoff)
                continue
            else:
                return {"error": f"request_error: {repr(last_exc)}", "url": OLLAMA_URL, "model": MODEL_NAME}

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
            return {"error": f"http_error {resp.status_code}: {body}", "url": OLLAMA_URL, "model": MODEL_NAME}

        # Parse JSON response
        try:
            return resp.json()
        except Exception:
            logger.error("Invalid JSON response from Ollama at %s (status %s)", OLLAMA_URL, resp.status_code)
            return {"error": f"invalid_json_response (status {resp.status_code})", "url": OLLAMA_URL, "model": MODEL_NAME}


async def generate_book_summary(book_data: dict) -> str:
    """Generate a book summary using Ollama. Falls back to a simple summary if the model is not available or the call fails."""
    prompt = f"""
Generate a concise and professional summary for the following book.

Title: {book_data.get('title')}
Author: {book_data.get('author')}
Genre: {book_data.get('genre')}
Year: {book_data.get('year_published')}
"""

    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    try:
        result = await _call_ollama(payload)
    except Exception as exc:
        # Catch any unexpected exception to avoid crashing the request flow
        print(f"Ollama request failed with exception: {exc}")
        return _fallback_book_summary(book_data)

    # Handle Ollama errors
    if not isinstance(result, dict):
        print("Ollama returned unexpected non-dict response")
        return _fallback_book_summary(book_data)
    if result.get("error"):
        # Example messages: "model 'llama3' not found" or http/network errors
        print("Ollama returned error:", result.get("error"))
        return _fallback_book_summary(book_data)

    # Successful response expected to include 'response' key
    ai_text = result.get("response") or result.get("text") or ""
    if not ai_text:
        return _fallback_book_summary(book_data)
    return ai_text


async def generate_review_summary(reviews: List[str]) -> str:
    """Generate a review summary using Ollama; fallback to simple summary on failure."""
    joined_reviews = "\n".join(reviews)
    prompt = f"""
Summarize the following book reviews. Highlight overall sentiment, positives, and negatives.

Reviews:
{joined_reviews}
"""

    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    try:
        result = await _call_ollama(payload)
    except Exception as exc:
        print(f"Ollama request failed with exception: {exc}")
        return _fallback_review_summary(reviews)

    if not isinstance(result, dict):
        print("Ollama returned unexpected non-dict response for reviews")
        return _fallback_review_summary(reviews)
    if result.get("error"):
        print("Ollama returned error for reviews:", result.get("error"))
        return _fallback_review_summary(reviews)

    ai_text = result.get("response") or result.get("text") or ""
    if not ai_text:
        return _fallback_review_summary(reviews)
    return ai_text
