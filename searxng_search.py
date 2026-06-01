#!/usr/bin/env python3
"""
SearXNG Search Tool - Meta-search via self-hosted SearXNG instance
Author: OpenCode Agent (Qwen 3.6 27b)
Created: 2026-05-31

This tool provides automated web search capabilities using a local SearXNG instance.
SearXNG aggregates results from 70+ search engines (Google, Bing, Brave, DDG, etc.).
No API key required. Requires a running SearXNG instance (see deploy_searxng.sh).

Requires: httpx (pre-installed on RHEL host)

Usage:
    python searxng_search.py "your query"
    python searxng_search.py "your query" --max-results 10
    python searxng_search.py "your query" --output json
    python searxng_search.py "your query" --engines google,brave
    python searxng_search.py "your query" --time-range month
"""

import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict, Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx library not installed.")
    print("\nPlease install with: pip3 install httpx")
    sys.exit(1)

DEFAULT_INSTANCE = "http://10.10.0.20:8080"
CONNECT_TIMEOUT = 8.0
READ_TIMEOUT = 15.0


class SearXNGSearch:
    """Search tool using a local SearXNG instance."""

    def __init__(self, instance_url: str = DEFAULT_INSTANCE):
        self.instance_url = instance_url.rstrip("/")
        self.client = httpx.Client(timeout=READ_TIMEOUT, follow_redirects=True)

    def health_check(self) -> bool:
        """Check if the SearXNG instance is reachable."""
        try:
            resp = self.client.get(f"{self.instance_url}/", timeout=CONNECT_TIMEOUT)
            return resp.status_code == 200
        except Exception:
            return False

    def search(
        self,
        query: str,
        max_results: int = 5,
        engines: Optional[str] = None,
        categories: Optional[str] = None,
        time_range: Optional[str] = None,
        language: str = "en",
        safesearch: int = 1,
    ) -> List[Dict]:
        """
        Perform a web search via SearXNG.

        Args:
            query: Search query string
            max_results: Max results to return (default: 5)
            engines: Comma-separated engine names (e.g. "google,brave,duckduckgo")
            categories: Comma-separated categories (general, news, images, etc.)
            time_range: Time filter (day, month, year)
            language: Language code (default: en)
            safesearch: 0=off, 1=moderate, 2=strict

        Returns:
            List of result dictionaries with title, url, content, engine fields
        """
        params = {
            "q": query,
            "format": "json",
            "language": language,
            "safesearch": safesearch,
        }
        if engines:
            params["engines"] = engines
        if categories:
            params["categories"] = categories
        if time_range:
            params["time_range"] = time_range

        try:
            resp = self.client.get(f"{self.instance_url}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])[:max_results]
            return results
        except httpx.ConnectError:
            print(f"ERROR: Cannot connect to SearXNG at {self.instance_url}", file=sys.stderr)
            print("Is the SearXNG container running on the AI-box?", file=sys.stderr)
            return []
        except httpx.HTTPStatusError as e:
            print(f"ERROR: SearXNG returned HTTP {e.response.status_code}", file=sys.stderr)
            return []
        except json.JSONDecodeError:
            print("ERROR: Invalid JSON response from SearXNG", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Search error: {e}", file=sys.stderr)
            return []

    def search_news(
        self,
        query: str,
        max_results: int = 5,
        time_range: Optional[str] = None,
    ) -> List[Dict]:
        """Search for news articles via SearXNG."""
        return self.search(
            query=query,
            max_results=max_results,
            categories="news",
            time_range=time_range,
        )

    def format_results_text(self, results: List[Dict], query: str) -> str:
        """Format results as readable text."""
        output = []
        output.append("=" * 80)
        output.append(f"SEARCH RESULTS: {query}")
        output.append(f"Source: SearXNG ({self.instance_url})")
        output.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Results Found: {len(results)}")
        output.append("=" * 80)
        output.append("")

        for i, r in enumerate(results, 1):
            title = r.get("title", "No Title")
            href = r.get("url", "No URL")
            content = r.get("content", "No description available")
            engine = r.get("engine", "unknown")
            if content:
                content = content[:250] + "..." if len(content) > 250 else content
            output.append(f"{i}. {title}")
            output.append(f"   URL: {href}")
            output.append(f"   Engine: {engine}")
            output.append(f"   {content}")
            output.append("")

        return "\n".join(output)

    def format_results_json(self, results: List[Dict], query: str) -> str:
        """Format results as JSON."""
        output = {
            "query": query,
            "source": "searxng",
            "instance": self.instance_url,
            "timestamp": datetime.now().isoformat(),
            "result_count": len(results),
            "results": results,
        }
        return json.dumps(output, indent=2)

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __del__(self):
        try:
            self.client.close()
        except Exception:
            pass


def interactive_mode(search_tool: SearXNGSearch):
    """Run in interactive mode."""
    print("\n" + "=" * 80)
    print("INTERACTIVE SEARXNG SEARCH")
    print(f"Instance: {search_tool.instance_url}")
    print("Type 'quit' or 'exit' to stop")
    print("=" * 80 + "\n")

    while True:
        try:
            query = input("Search query: ").strip()
            if query.lower() in ("quit", "exit", "q"):
                print("\nGoodbye!")
                break
            if not query:
                continue
            print("\nSearching...")
            results = search_tool.search(query, max_results=5)
            if results:
                print(search_tool.format_results_text(results, query))
            else:
                print("No results found.\n")
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="SearXNG Search Tool - Meta-search via local SearXNG instance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python searxng_search.py "OpenShift networking best practices"
  python searxng_search.py "CUDA memory optimization" --max-results 10
  python searxng_search.py "latest news" --output json
  python searxng_search.py "Python async" --engines google,brave
  python searxng_search.py "recent events" --time-range month
  python searxng_search.py --interactive
        """,
    )

    parser.add_argument("query", nargs="?", help="Search query string")
    parser.add_argument("--max-results", "-n", type=int, default=5, help="Max results (default: 5)")
    parser.add_argument("--output", "-o", choices=["text", "json"], default="text", help="Output format (default: text)")
    parser.add_argument("--time-range", "-t", choices=["day", "month", "year"], help="Time filter")
    parser.add_argument("--news", action="store_true", help="Search news only")
    parser.add_argument("--engines", help="Comma-separated engine names (e.g. google,brave,duckduckgo)")
    parser.add_argument("--categories", help="Comma-separated categories (general, news, images, videos, etc.)")
    parser.add_argument("--instance", default=DEFAULT_INSTANCE, help=f"SearXNG instance URL (default: {DEFAULT_INSTANCE})")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--save", "-s", metavar="FILE", help="Save results to file")

    args = parser.parse_args()

    search_tool = SearXNGSearch(instance_url=args.instance)

    if not search_tool.health_check():
        print(f"ERROR: SearXNG instance unreachable at {args.instance}", file=sys.stderr)
        print("Deploy SearXNG first: see deploy_searxng.sh", file=sys.stderr)
        sys.exit(1)

    if args.interactive:
        interactive_mode(search_tool)
        return

    if not args.query:
        parser.print_help()
        print("\nERROR: Search query required (unless using --interactive)")
        sys.exit(1)

    print(f"Searching for: {args.query}\n")

    if args.news:
        results = search_tool.search_news(args.query, max_results=args.max_results, time_range=args.time_range)
    else:
        results = search_tool.search(
            args.query,
            max_results=args.max_results,
            engines=args.engines,
            categories=args.categories,
            time_range=args.time_range,
        )

    if not results:
        print("No results found.")
        sys.exit(0)

    if args.output == "json":
        output = search_tool.format_results_json(results, args.query)
    else:
        output = search_tool.format_results_text(results, args.query)

    print(output)

    if args.save:
        try:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"\nResults saved to: {args.save}")
        except Exception as e:
            print(f"\nError saving file: {e}", file=sys.stderr)

    search_tool.close()


if __name__ == "__main__":
    main()
