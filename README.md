# pinterest-vision-mcp

> Pinterest visual intelligence pipeline as an MCP server — search, download, analyze, store, retrieve.

An MCP server that builds a searchable library of visual references from Pinterest. Search for images, download them, analyze them with LLM vision (structured aesthetic tags), store in a vector database, and retrieve by semantic similarity.

## Requirements

- Python 3.10+
- API key for any **OpenAI-compatible vision API** (OpenRouter, OpenAI, Groq, Mistral, etc.)

> **Cost note:** Image analysis calls an LLM API and incurs a small cost per image. With `claude-sonnet-4-6` via OpenRouter, analyzing 8 images costs roughly $0.01–$0.05. With `gpt-4o-mini` via OpenAI it's even cheaper.

## Installation

```bash
# 1. Clone
git clone https://github.com/Kreminskaya90/pinterest-vision-mcp.git
cd pinterest-vision-mcp

# 2. Install
pip install -e .

# 3. Configure
cp .env.example .env
# Edit .env and set your OPENROUTER_API_KEY
```

## Running the MCP server

```bash
python -m pinterest_vision_mcp.server
```

Or add to your MCP client config (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "pinterest-vision": {
      "command": "python",
      "args": ["-m", "pinterest_vision_mcp.server"],
      "cwd": "/path/to/pinterest-vision-mcp",
      "env": {
        "OPENROUTER_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `VISION_API_KEY` | — | **Required.** API key for your LLM provider |
| `VISION_API_BASE_URL` | `https://openrouter.ai/api/v1` | Base URL of any OpenAI-compatible API |
| `PINTEREST_VISION_MODEL` | `anthropic/claude-sonnet-4-6` | Any vision-capable model from your provider |
| `PINTEREST_DATA_DIR` | `./data` | Directory for downloaded images |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB vector storage path |

**Supported providers (any OpenAI-compatible API):**
```
# OpenRouter (access to 200+ models)
VISION_API_BASE_URL=https://openrouter.ai/api/v1
PINTEREST_VISION_MODEL=anthropic/claude-sonnet-4-6

# OpenAI directly
VISION_API_BASE_URL=https://api.openai.com/v1
PINTEREST_VISION_MODEL=gpt-4o-mini

# Groq
VISION_API_BASE_URL=https://api.groq.com/openai/v1
PINTEREST_VISION_MODEL=llama-3.2-11b-vision-preview
```

## Available tools

| Tool | Description |
|---|---|
| `pinterest_search` | Search Pinterest by query, returns pins with image URLs |
| `pinterest_download` | Download images from search results to local disk |
| `pinterest_analyze` | Analyze images with LLM vision, returns structured tags |
| `pinterest_ingest` | Store analyses in ChromaDB for future retrieval |
| `pinterest_pipeline` | Full pipeline in one call: search → download → analyze → store |
| `visual_search` | Semantic search across stored visual references |

## Visual analysis tags

Each analyzed image returns:

| Tag | Example values |
|---|---|
| `lighting_type` | natural, studio, golden hour, overcast |
| `composition_type` | centered, rule-of-thirds, flat lay, symmetrical |
| `camera_distance` | close-up, medium, full body, detail shot |
| `mood` | editorial, minimal, dark, romantic, energetic |
| `palette` | color description |
| `segment` | luxury / premium / contemporary / streetwear |
| `shot_type` | campaign editorial / e-commerce product / lookbook |
| `garment_focus` | what clothing items are featured |
| `styling_signals` | styling details and accessories |
| `brand_feel` | brand aesthetic impression |
| `overall_quality` | reference-worthy / average / not useful |
| `raw_description` | 2-3 sentence summary |

## First run note

On the first call to `pinterest_ingest` or `pinterest_pipeline` (with `ingest=True`), ChromaDB will automatically download a sentence transformer embedding model (~90 MB). This happens once and is cached locally.

## Example usage

```python
# Full pipeline — one call does everything
result = pinterest_pipeline(
    query="quiet luxury beige coat editorial",
    limit=15,
    max_download=8,
)
# result.summary: "Complete: 15 found, 8 downloaded, 8 analyzed, 8 stored"

# Semantic search in stored references
refs = visual_search(
    query="dark masculine editorial close-up",
    segment="luxury",
    shot_type="campaign editorial",
)
```

## Disclaimer

This tool uses the `pinterest-dl` library for Pinterest access. Use responsibly and in accordance with Pinterest's [Terms of Service](https://policy.pinterest.com/en/terms-of-service). Intended for research and educational purposes.
