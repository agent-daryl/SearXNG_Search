# SearXNG Deployment and Search Tools

## Overview

Dual-backend search: **SearXNG** (primary, meta-search from 70+ engines) with **DuckDuckGo** fallback.

| Tool | Location | Backend | Status |
|---|---|---|---|
| `search.py` | `tools/Web_Search/search.py` | SearXNG → DDG fallback | Ready (needs SearXNG running) |
| `searxng_search.py` | `tools/SearXNG_Search/searxng_search.py` | SearXNG only | Ready (needs SearXNG running) |
| `web_search.py` | `tools/Web_Search/web_search.py` | DuckDuckGo only | Working (legacy) |

## Deploy SearXNG on AI-box

SearXNG is lightweight (~100-200 MB RAM), won't affect inference.

SSH into the AI-box and run:

```bash
docker run -d \
  --name searxng \
  --restart=unless-stopped \
  -p 8080:8080 \
  -e SEARXNG_BASE_URL=http://10.10.0.20:8080/ \
  searxng/searxng:latest
```

Verify it's running:

```bash
docker logs searxng | tail -5
curl -s http://localhost:8080 | head -5
```

**Port note:** AI-box port 8080 is free (open-webui maps 3000→8080 internally).

## Usage

### Dispatcher (recommended — SearXNG primary, DDG fallback)

```bash
cd tools/Web_Search

# Basic search
python3 search.py "OpenShift networking best practices"

# More results, JSON output
python3 search.py "CUDA memory optimization" -n 10 -o json

# News search, time filter
python3 search.py "AI news" --news -t w

# Save results
python3 search.py "Python async patterns" -s results.txt
```

### Direct SearXNG (skip fallback)

```bash
cd tools/SearXNG_Search

# Basic search
python3 searxng_search.py "your query"

# Specific engines
python3 searxng_search.py "VMware migration" --engines google,brave,duckduckgo

# Interactive
python3 searxng_search.py --interactive
```

### Legacy DDG-only (still works)

```bash
python3 tools/Web_Search/web_search.py "your query"
```

## Architecture

```
search.py (dispatcher)
  ├── SearXNG instance @ 10.10.0.20:8080 ← 70+ engines (Google, Bing, Brave, etc.)
  └── DuckDuckGo (fallback via ddgs library)
```

## Configuration

No config file needed. Change `DEFAULT_INSTANCE` in either `.py` file, or override with `--instance` flag.

## SearXNG Engine Selection

If you want to tune which engines SearXNG uses, mount a custom `settings.yml`:

```bash
docker run -d \
  --name searxng \
  --restart=unless-stopped \
  -p 8080:8080 \
  -v /path/to/settings.yml:/etc/searxng/settings.yml \
  -e SEARXNG_BASE_URL=http://10.10.0.20:8080/ \
  searxng/searxng:latest
```

Default settings work great out of the box — only customize if you want to disable specific engines or add API keys for better results.


---

> **Privacy note:** Internal IP addresses originally present in this repository have been replaced with placeholder addresses in the `10.10.0.0/16` range to protect the owner's private network topology. Functionality is unchanged; configure real addresses via environment variables where supported.
