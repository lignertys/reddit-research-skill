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

| Request | Returned | Created range | Server time |
|---|---|---|---|
| `vector limit=30` | 30 | 2026-01-02 .. 2026-07-30 | 3.2s (cold connection) |
| `vector limit=100` | 100 | 2026-01-01 .. 2026-07-30 | 0.8s |
| `vector limit=20`, window `2026-01-01..2026-03-31` | 20, none outside the window | 2026-01-02 .. 2026-03-01 | 0.6s |
| `semantic limit=100` | 100 | - | 2.3s |
| MCP `reddit_vector_search limit=100` | 100 | 2026-01-01 .. 2026-07-30 | 2.2s wall |

No malformed rows, no duplicate ids, no empty `content` in any of the above.

`upvotes`/`comments` come from the vector index metadata (recorded at index time),
not a live read. Cross-checked against the live post table for the same 100 ids: 52
were still in that table, of which 50 matched exactly and 2 differed only in comment
count; no case where the API reported 0 upvotes while the table had more. The other
48 were archive rows the live table no longer holds - which is exactly why earlier
measurements of this endpoint topped out near 52.

`sentiment` on semantic results was an empty string in every case.

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
