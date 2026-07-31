#!/usr/bin/env bash
# CLI for reddapi.dev. Requires REDDAPI_API_KEY to be set.
#
# Usage:
#   ./reddapi-cli.sh search "productivity tools" [--limit N] [--mode vector|semantic] \
#                     [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]
#   ./reddapi-cli.sh trends [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--limit N]
#   ./reddapi-cli.sh subreddits [--limit N]
#   ./reddapi-cli.sh subreddit <name>
#
# Defaults: search mode=vector, limit=20; trends defaults to the last 30 days.
# Search limit is capped server-side at 100 for both modes (higher values are
# clamped silently), trends at 100.

set -euo pipefail

BASE="https://reddapi.dev"
API_BASE="$BASE/api/v1"

if [ -z "${REDDAPI_API_KEY:-}" ]; then
  echo "Error: REDDAPI_API_KEY is not set. Get a key at https://reddapi.dev" >&2
  exit 1
fi

fail_on_error() {
  local http_code="$1" body="$2"
  if [ "$http_code" -ge 400 ]; then
    echo "HTTP $http_code" >&2
    echo "$body" >&2
    case "$http_code" in
      403) echo "Hint: POST requests need Content-Type: application/json (handled by this script already - check the endpoint path)." >&2 ;;
      404) echo "Hint: check method+path. /trends and /search/* are POST under /api/v1; subreddits are GET and exist under both /api and /api/v1." >&2 ;;
      429) echo "Hint: invalid/expired key or plan quota exhausted. This API also returns 429 for bad keys, not 401." >&2 ;;
    esac
    exit 1
  fi
}

# Feeds the Authorization header to curl through a stdin config file instead of
# an -H argument, so the key never lands in the process list (argv is readable
# by any user via ps) and never appears in shell history or logs.
curl_auth() {
  printf 'header = "Authorization: Bearer %s"\n' "$REDDAPI_API_KEY" \
    | curl --config - "$@"
}

post_json() {
  local path="$1" body="$2"
  local tmp; tmp="$(mktemp)"
  local code
  code=$(curl_auth -s -o "$tmp" -w "%{http_code}" -X POST "$API_BASE$path" \
    -H "Content-Type: application/json" \
    -d "$body")
  local out; out="$(cat "$tmp")"; rm -f "$tmp"
  fail_on_error "$code" "$out"
  echo "$out"
}

get_json() {
  local url="$1"
  local tmp; tmp="$(mktemp)"
  local code
  code=$(curl_auth -s -o "$tmp" -w "%{http_code}" "$url")
  local out; out="$(cat "$tmp")"; rm -f "$tmp"
  fail_on_error "$code" "$out"
  echo "$out"
}

cmd="${1:-}"
shift || true

case "$cmd" in
  search)
    query="${1:-}"
    [ -z "$query" ] && { echo "Usage: $0 search \"query\" [--limit N] [--mode vector|semantic] [--start-date D] [--end-date D]" >&2; exit 1; }
    shift || true
    limit=20
    mode="vector"
    start_date=""
    end_date=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --limit) limit="$2"; shift 2 ;;
        --mode) mode="$2"; shift 2 ;;
        --start-date) start_date="$2"; shift 2 ;;
        --end-date) end_date="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
      esac
    done
    endpoint="/search/vector"
    [ "$mode" = "semantic" ] && endpoint="/search/semantic"
    body="{\"query\": $(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$query"), \"limit\": $limit"
    [ -n "$start_date" ] && body="$body, \"start_date\": \"$start_date\""
    [ -n "$end_date" ] && body="$body, \"end_date\": \"$end_date\""
    body="$body}"
    post_json "$endpoint" "$body"
    ;;

  trends)
    limit=10
    start_date=""
    end_date=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --limit) limit="$2"; shift 2 ;;
        --start-date) start_date="$2"; shift 2 ;;
        --end-date) end_date="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
      esac
    done
    # Default window: last 30 days, computed at run time (portable date arithmetic).
    if [ -z "$end_date" ]; then
      end_date=$(date -u +%Y-%m-%d)
    fi
    if [ -z "$start_date" ]; then
      if date -v-30d >/dev/null 2>&1; then
        start_date=$(date -u -v-30d +%Y-%m-%d)   # BSD/macOS date
      else
        start_date=$(date -u -d "-30 days" +%Y-%m-%d)  # GNU date
      fi
    fi
    body="{\"start_date\": \"$start_date\", \"end_date\": \"$end_date\", \"limit\": $limit}"
    post_json "/trends" "$body"
    ;;

  subreddits)
    limit=50
    while [ $# -gt 0 ]; do
      case "$1" in
        --limit) limit="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
      esac
    done
    # Public variant on purpose: /api/subreddits needs no key and does not consume
    # quota. The keyed /api/v1/subreddits also exists (adds sort/order/icon).
    get_json "$BASE/api/subreddits?limit=$limit"
    ;;

  subreddit)
    name="${1:-}"
    [ -z "$name" ] && { echo "Usage: $0 subreddit <name>" >&2; exit 1; }
    get_json "$BASE/api/subreddits/$name"
    ;;

  *)
    echo "Usage: $0 {search|trends|subreddits|subreddit} ..." >&2
    echo "See SKILL.md for full documentation." >&2
    exit 1
    ;;
esac
