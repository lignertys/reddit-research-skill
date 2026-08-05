#!/usr/bin/env python3
"""Query the reddapi.dev HTTP API. Stdlib only, no third-party imports.

Reads the API key from REDDAPI_API_KEY and never prints it.

    python3 reddapi.py vector "frustrated with project management tools" --limit 100
    python3 reddapi.py vector "AI coding agents" --start 2026-01-01 --end 2026-07-30
    python3 reddapi.py semantic "best productivity tools for remote teams" --summary
    python3 reddapi.py trends --start 2026-07-01 --end 2026-07-30 --limit 10
    python3 reddapi.py subreddits --search programming --limit 100
    python3 reddapi.py subreddit programming

Add --raw to print the untouched JSON response instead of the digest.
Exit codes: 0 ok, 1 API/network error, 2 missing credentials.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("REDDAPI_BASE_URL", "https://reddapi.dev").rstrip("/")
TIMEOUT = float(os.environ.get("REDDAPI_TIMEOUT", "120"))

# limit ceilings the server clamps to, mirrored here so the caller sees the
# clamp instead of silently asking for something it will not get
MAX_LIMIT = {"vector": 100, "semantic": 100, "trends": 100, "subreddits": 100}


class MissingKey(RuntimeError):
    """REDDAPI_API_KEY is not set in the environment."""


class ApiError(RuntimeError):
    """The API returned a non-2xx status or an error envelope."""


def _api_key() -> str:
    key = os.environ.get("REDDAPI_API_KEY", "").strip()
    if not key:
        raise MissingKey(
            "REDDAPI_API_KEY is not set. Export it in your own shell "
            "(value from https://reddapi.dev/account) and retry."
        )
    return key


def _clamp(value: int, endpoint: str) -> int:
    return max(1, min(int(value), MAX_LIMIT[endpoint]))


def request(method: str, path: str, *, body: dict | None = None,
            params: dict | None = None, auth: bool = True) -> dict:
    """Send one request and return the decoded JSON body.

    POST bodies always carry Content-Type: application/json; without it the
    server answers 403 ("Cross-site POST form submissions are forbidden"),
    which is a header problem and not a plan limit.
    """
    url = f"{BASE_URL}{path}"
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url = f"{url}?{urllib.parse.urlencode(clean)}"

    headers = {"Accept": "application/json"}
    if auth:
        headers["Authorization"] = f"Bearer {_api_key()}"

    data = None
    if body is not None:
        # send at least {}; an empty POST body is parsed as JSON and 500s
        data = json.dumps({k: v for k, v in body.items() if v is not None}).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # report status + body only, never the request headers (they hold the key)
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise ApiError(f"HTTP {exc.code} from {path}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"cannot reach {BASE_URL}: {exc.reason}") from exc

    if isinstance(payload, dict) and payload.get("success") is False:
        raise ApiError(f"api error from {path}: {payload.get('error', 'unknown')}")
    return payload


def vector(query: str, limit: int = 30, start_date: str | None = None,
           end_date: str | None = None) -> dict:
    """Nearest-neighbour search over the full archive. Honours date filters."""
    return request("POST", "/api/v1/search/vector",
                   body={"query": query, "limit": _clamp(limit, "vector"),
                         "start_date": start_date, "end_date": end_date})


def semantic(query: str, limit: int = 20, include_summary: bool = False) -> dict:
    """LLM-assisted search. No date filter; summary is opt-in and slow."""
    body = {"query": query, "limit": _clamp(limit, "semantic")}
    if include_summary:
        body["include_summary"] = True
    return request("POST", "/api/v1/search/semantic", body=body)


def trends(start_date: str | None = None, end_date: str | None = None,
           limit: int = 20) -> dict:
    """Site-wide momentum. POST only; both dates default to today, so pass a range."""
    return request("POST", "/api/v1/trends",
                   body={"start_date": start_date, "end_date": end_date,
                         "limit": _clamp(limit, "trends")})


def subreddits(search: str | None = None, limit: int = 20, page: int = 1,
               sort: str | None = None, order: str | None = None) -> dict:
    """List subreddits.

    Uses the public /api/subreddits route (no auth, no quota) unless sort or
    order is requested, which only the metered /api/v1 route supports.
    """
    if sort or order:
        return request("GET", "/api/v1/subreddits",
                       params={"search": search, "limit": _clamp(limit, "subreddits"),
                               "page": page, "sort": sort or "subscribers",
                               "order": order or "desc"})
    return request("GET", "/api/subreddits", auth=False,
                   params={"search": search, "limit": _clamp(limit, "subreddits"),
                           "page": page})


def subreddit(name: str, metered: bool = False) -> dict:
    """Detail for one subreddit. Public route returns recentPosts, /v1 recent_posts."""
    slug = urllib.parse.quote(name.lstrip("/").removeprefix("r/"))
    if metered:
        return request("GET", f"/api/v1/subreddits/{slug}")
    return request("GET", f"/api/subreddits/{slug}", auth=False)


def digest_search(payload: dict) -> str:
    """One line per post: score, subreddit, engagement, title, url."""
    data = payload.get("data", payload)
    lines = []
    for item in data.get("results") or []:
        score = item.get("similarity_score", item.get("relevance"))
        score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "-.--"
        lines.append(
            f"[{score_str}] r/{item.get('subreddit', '?')} "
            f"{item.get('upvotes', 0)}up {item.get('comments', 0)}c "
            f"{item.get('created', '')[:10]} {item.get('title', '')}\n"
            f"    {item.get('url', '')}"
        )
    summary = data.get("ai_summary")
    if summary:
        lines.append(f"\nAI summary:\n{summary}")
    if not lines:
        return "(no results)"
    lines.append(f"\n{data.get('total', len(lines))} returned in "
                 f"{data.get('processing_time_ms', '?')}ms")
    return "\n".join(lines)


def digest_trends(payload: dict) -> str:
    data = payload.get("data", payload)
    rows = data.get("trends") or []
    if not rows:
        return "(no trends for that range)"
    return "\n".join(
        f"{t.get('topic', '?')}: {t.get('growth_rate', 0)}% growth, "
        f"{t.get('post_count', 0)} posts, score {t.get('trend_score', 0)}, "
        f"top r/{'/'.join((t.get('top_subreddits') or ['?'])[:2])}"
        for t in rows
    )


def digest_subreddits(payload: dict) -> str:
    data = payload.get("data", payload)
    rows = data.get("subreddits") or []
    if not rows:
        return "(no subreddits)"
    head = "\n".join(
        f"r/{s.get('name', '?')}  {s.get('subscribers', 0)} subs  "
        f"{(s.get('title') or '')[:60]}"
        for s in rows
    )
    return f"{head}\n\npage {data.get('page', 1)}/{data.get('total_pages', 1)}, " \
           f"{data.get('total', len(rows))} total"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="reddapi.dev CLI")
    parser.add_argument("--raw", action="store_true", help="print raw JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("vector", help="archive search with date filtering (default)")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--start", dest="start_date")
    p.add_argument("--end", dest="end_date")

    p = sub.add_parser("semantic", help="LLM-assisted search, no date filter")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--summary", action="store_true", help="request data.ai_summary")

    p = sub.add_parser("trends", help="site-wide momentum for a date range")
    p.add_argument("--start", dest="start_date")
    p.add_argument("--end", dest="end_date")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("subreddits", help="list subreddits (free unless sorted)")
    p.add_argument("--search")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--sort", choices=["subscribers", "created"])
    p.add_argument("--order", choices=["asc", "desc"])

    p = sub.add_parser("subreddit", help="detail for one subreddit")
    p.add_argument("name")
    p.add_argument("--metered", action="store_true",
                   help="use the /v1 route (counts against quota)")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "vector": (lambda a: vector(a.query, a.limit, a.start_date, a.end_date),
                   digest_search),
        "semantic": (lambda a: semantic(a.query, a.limit, a.summary), digest_search),
        "trends": (lambda a: trends(a.start_date, a.end_date, a.limit), digest_trends),
        "subreddits": (lambda a: subreddits(a.search, a.limit, a.page, a.sort, a.order),
                       digest_subreddits),
        "subreddit": (lambda a: subreddit(a.name, a.metered),
                      lambda p: json.dumps(p, indent=2, ensure_ascii=False)),
    }
    call, render = handlers[args.command]
    try:
        payload = call(args)
    except MissingKey as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.raw
          else render(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
