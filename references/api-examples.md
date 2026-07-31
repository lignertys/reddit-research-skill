# reddapi.dev API Examples

Real request/response pairs, captured 2026-07-31 against the live API using
`scripts/reddapi-cli.sh` and raw `curl`. Use these to sanity-check integration -
if a live response no longer matches this shape, the API changed and this file
(and `SKILL.md`) needs updating.

## Vector search

```bash
curl -X POST "https://reddapi.dev/api/v1/search/vector" \
  -H "Authorization: Bearer $REDDAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "adult coloring app stress relief", "limit": 1}'
```

```json
{
  "success": true,
  "data": {
    "query": "adult coloring app stress relief",
    "results": [
      {
        "id": "1ubmu5n",
        "title": "Birb",
        "content": "Pen and paper\n\nDigital coloring",
        "subreddit": "doodles",
        "upvotes": 9,
        "comments": 0,
        "created": "2026-06-21T10:39:42.000Z",
        "similarity_score": 0.7542883157730103,
        "url": "https://reddit.com/r/doodles/comments/1ubmu5n"
      }
    ],
    "total": 1,
    "processing_time_ms": 976
  }
}
```

## Trends (30-day window)

```bash
curl -X POST "https://reddapi.dev/api/v1/trends" \
  -H "Authorization: Bearer $REDDAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2026-07-01", "end_date": "2026-07-30", "limit": 2}'
```

Returned `data.trends[].topic` values in this capture: `general`, `years` - trends
are global site-wide momentum, not scoped to a query or subreddit; do not expect
topic-relevant results from this endpoint alone.

## Subreddit list

```bash
curl "https://reddapi.dev/api/subreddits?limit=3" \
  -H "Authorization: Bearer $REDDAPI_API_KEY"
```

Returned (truncated): `announcements`, `funny`, `askreddit`. The `Authorization`
header is harmless but unnecessary here: this path is public and does not consume
quota. The keyed variant `/api/v1/subreddits` exists too and adds
`sort`/`order`/`icon`; both wrap the list as `data.subreddits[]` with `total`,
`page`, `limit`, `total_pages`.

## Subreddit detail

```bash
curl "https://reddapi.dev/api/subreddits/programming" \
  -H "Authorization: Bearer $REDDAPI_API_KEY"
```

```json
{
  "success": true,
  "data": {
    "name": "programming",
    "title": "programming",
    "description": "Computer Programming",
    "subscribers": 6906183,
    "created": "2006-02-28T18:...",
    "recentPosts": ["... 10 most recent posts, elided here ..."]
  }
}
```

`/api/v1/subreddits/programming` returns the same data but names that array
`recent_posts` (snake_case).

## Measured limit behaviour (live, 2026-07-31, one paid key)

Query: "people frustrated with project management tools".

| Request | Returned | Wall time |
|---|---|---|
| `vector limit=5` | 4 | 6.3s (cold connection) |
| `vector limit=30` | 17 | 2.4s |
| `vector limit=100` | 52 | 1.3s |
| `vector limit=250` | 52 (clamped to 100) | 1.8s |
| `semantic limit=100` | 100 | 3.4s |

Cold-cache run with a never-before-seen query: `vector limit=100` → 40 results in
2.6s, `semantic limit=100` → 100 results in 2.9s. So the vector shortfall is not a
cache artifact: the endpoint rehydrates hits from a rolling post table covering
2026-06-19 onward and drops older archive hits. `sentiment` on semantic results was
an empty string in every case.

## Common errors (all captured live)

| Trigger | Response |
|---|---|
| POST without `Content-Type: application/json` | `HTTP 403` - "Cross-site POST form submissions are forbidden" |
| `GET /api/v1/trends` | `HTTP 404` (HTML page, not JSON) - the route is POST-only, so this is about the method, not the missing body |
| POST with an empty body | `HTTP 500` - the body is JSON-parsed unconditionally; send `{}` at minimum |
| Invalid/expired API key | `HTTP 429` - `{"success":false,"error":"Rate limit exceeded","message":{"title":"API Access Required",...},"rateLimitInfo":{"limit":0,"remaining":0,"resetAt":0}}` - note this is 429, not 401 |

## Verifying this file still holds

```bash
export REDDAPI_API_KEY="your_key"
../scripts/reddapi-cli.sh search "test query" --limit 1
../scripts/reddapi-cli.sh trends --limit 1
../scripts/reddapi-cli.sh subreddits --limit 1
../scripts/reddapi-cli.sh subreddit programming
```
