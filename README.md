# Exa Pool MCP Server

Remote MCP server wrapping [ExaFree](https://github.com/chengtx809/ExaFree) API as Streamable HTTP service.

Deployed on the same server as ExaFree for localhost access (no public API key needed).

## Tools

| Tool | Description |
|------|-------------|
| `exa_search` | AI-powered web search |
| `exa_get_contents` | Fetch clean page content |
| `exa_find_similar` | Find similar pages |
| `exa_answer` | AI-generated answer with citations |
| `exa_create_research` | Create async deep research task |
| `exa_get_research` | Get research task results |

## Deploy

```bash
# On the same server as ExaFree
export EXA_POOL_BASE_URL="http://127.0.0.1:7860"
export EXA_POOL_API_KEY="your-key"
export PORT=3101

uv run server.py
```

## MCP Config

```json
{
  "mcpServers": {
    "exa-pool": {
      "type": "http",
      "url": "http://10.0.8.20:3101/mcp"
    }
  }
}
```
