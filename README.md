# pinterest-vision-mcp

> Pinterest visual intelligence pipeline as an MCP server — search, download, analyze, store, retrieve.

An MCP server that builds a searchable library of visual references from Pinterest. Search for images, download them, analyze them with LLM vision (structured fashion/aesthetic tags), store in a vector database, and retrieve by semantic similarity.

## Installation

```bash
# 1. Clone
git clone https://github.com/Kreminskaya90/pinterest-vision-mcp.git
cd pinterest-vision-mcp

# 2. Install
pip install -e .

# 3. Configure
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

## Running the MCP server

```bash
python -m pinterest_vision_mcp.server
```

Or add to your MCP client config:

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
| `OPENROUTER_API_KEY` | — | Required. Your OpenRouter API key |
| `PINTEREST_VISION_MODEL` | `anthropic/claude-sonnet-4-6` | LLM model for image analysis |
| `PINTEREST_DATA_DIR` | `./data` | Directory for downloaded images |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB storage path |

## Available tools

| Tool | Description |
|---|---|
| `pinterest_search` | Search Pinterest for pins by query |
| `pinterest_download` | Download images from search results to local disk |
| `pinterest_analyze` | Analyze images with LLM vision, returns structured tags |
| `pinterest_ingest` | Store analyses in ChromaDB vector base |
| `pinterest_pipeline` | Full pipeline in one call: search → download → analyze → ingest |
| `nasmotrennost_search` | Semantic search across stored visual references |

## Visual analysis tags

Each analyzed image returns:

- `lighting_type` — natural, studio, golden hour, etc.
- `composition_type` — centered, rule-of-thirds, flat lay, etc.
- `camera_distance` — close-up, medium, full body, etc.
- `mood` — editorial, minimal, dark, romantic, etc.
- `palette` — color description
- `segment` — luxury / premium / contemporary / streetwear
- `shot_type` — campaign editorial / e-commerce product / lookbook / etc.
- `garment_focus` — what clothing items are featured
- `styling_signals` — styling details
- `brand_feel` — brand aesthetic impression
- `overall_quality` — reference-worthy / average / not useful
- `raw_description` — 2-3 sentence summary

## Example usage

```python
# Full pipeline
result = pinterest_pipeline(
    query="quiet luxury beige coat editorial",
    limit=15,
    max_download=8,
)

# Semantic search in stored references
refs = nasmotrennost_search(
    query="dark masculine editorial close-up",
    segment="luxury",
    shot_type="campaign editorial",
)
```

## Disclaimer

This tool uses the `pinterest-dl` library for Pinterest access. Use responsibly and in accordance with Pinterest's [Terms of Service](https://policy.pinterest.com/en/terms-of-service). Intended for research and educational purposes.
