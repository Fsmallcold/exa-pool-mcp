# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp[cli]>=1.6.0",
#     "httpx>=0.27.0",
#     "uvicorn>=0.32.0",
# ]
# ///
"""
Exa Pool MCP Server (Remote HTTP)
Wraps the ExaFree API as a remote MCP service via Streamable HTTP.
Deployed on the same server as ExaFree for localhost access.
"""

from mcp.server.fastmcp import FastMCP
import httpx
import json
import logging
import os
from typing import Optional, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ExaFree runs on the same server
EXA_POOL_BASE_URL = os.getenv("EXA_POOL_BASE_URL", "http://127.0.0.1:7860")
EXA_POOL_API_KEY = os.getenv("EXA_POOL_API_KEY", "")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "3101"))

mcp = FastMCP("exa-pool")

TIMEOUT = httpx.Timeout(30.0, connect=5.0)


def format_error(status_code: int, message: str) -> str:
    return f"Error {status_code}: {message}"


def format_json(data: dict) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return str(data)


async def exa_request(
    endpoint: str,
    method: str = "POST",
    data: Optional[dict] = None,
    params: Optional[dict] = None,
) -> str:
    url = f"{EXA_POOL_BASE_URL.rstrip('/')}{endpoint}"
    headers = {
        "Authorization": f"Bearer {EXA_POOL_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            if method == "POST":
                response = await client.post(url, json=data, headers=headers)
            else:
                response = await client.get(url, params=params, headers=headers)

            if response.status_code == 401:
                return format_error(401, "Authentication failed.")
            if response.status_code == 429:
                return format_error(429, "Rate limited. Try again later.")
            if response.status_code >= 500:
                return format_error(response.status_code, "ExaFree server error.")

            response.raise_for_status()
            return format_json(response.json())

    except httpx.TimeoutException:
        return "Error: Request timed out (30s)."
    except httpx.ConnectError:
        return f"Error: Cannot connect to ExaFree at {EXA_POOL_BASE_URL}."
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@mcp.tool()
async def exa_search(
    query: str,
    num_results: int = 10,
    search_type: str = "auto",
    include_text: bool = False,
) -> str:
    """Search the web using Exa's AI-powered search engine.

    Args:
        query: Search query
        num_results: Number of results (1-100, default 10)
        search_type: "auto" (default), "neural", "fast", or "deep"
        include_text: Include page text content (default False)
    """
    if not query or not query.strip():
        return "Error: query is required"
    if not 1 <= num_results <= 100:
        return "Error: num_results must be 1-100"

    payload = {"query": query.strip(), "numResults": num_results, "type": search_type}
    if include_text:
        payload["contents"] = {"text": True}

    return await exa_request("/search", data=payload)


@mcp.tool()
async def exa_get_contents(
    urls: List[str], include_text: bool = True, include_html: bool = False
) -> str:
    """Get clean parsed content from web pages.

    Args:
        urls: List of URLs to fetch (max 100)
        include_text: Include cleaned text (default True)
        include_html: Include raw HTML (default False)
    """
    if not urls:
        return "Error: urls is required"
    if len(urls) > 100:
        return "Error: max 100 URLs"

    payload = {"urls": urls, "text": include_text}
    if include_html:
        payload["htmlContent"] = True

    return await exa_request("/contents", data=payload)


@mcp.tool()
async def exa_find_similar(
    url: str, num_results: int = 10, include_text: bool = False
) -> str:
    """Find web pages similar to a given URL.

    Args:
        url: Reference URL
        num_results: Number of results (1-100, default 10)
        include_text: Include page text (default False)
    """
    if not url:
        return "Error: url is required"

    payload = {"url": url.strip(), "numResults": num_results}
    if include_text:
        payload["contents"] = {"text": True}

    return await exa_request("/findSimilar", data=payload)


@mcp.tool()
async def exa_answer(query: str, include_text: bool = False) -> str:
    """Get AI-generated answer with citations.

    Args:
        query: Question to answer
        include_text: Include full text from sources (default False)
    """
    if not query:
        return "Error: query is required"

    return await exa_request("/answer", data={"query": query.strip(), "text": include_text})


@mcp.tool()
async def exa_create_research(instructions: str, model: str = "exa-research") -> str:
    """Create async deep research task.

    Args:
        instructions: Research task description (max 4096 chars)
        model: "exa-research-fast", "exa-research" (default), or "exa-research-pro"
    """
    if not instructions:
        return "Error: instructions is required"
    if len(instructions) > 4096:
        return "Error: max 4096 characters"

    return await exa_request("/research/v1", data={"instructions": instructions.strip(), "model": model})


@mcp.tool()
async def exa_get_research(research_id: str) -> str:
    """Get status/results of a research task.

    Args:
        research_id: Task ID from exa_create_research
    """
    if not research_id:
        return "Error: research_id is required"

    return await exa_request(f"/research/v1/{research_id.strip()}", method="GET")


if __name__ == "__main__":
    logger.info(f"Starting Exa Pool MCP on {HOST}:{PORT}")
    logger.info(f"ExaFree API: {EXA_POOL_BASE_URL}")
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
