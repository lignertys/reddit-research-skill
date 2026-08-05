# reddapi.dev API reference

Base URL `https://reddapi.dev`. Authenticated routes take
`Authorization: Bearer $REDDAPI_API_KEY`. Every POST must send
`Content-Type: application/json`.

Endpoint behaviour below was re-measured against the live service on
2026-07-31; the note under "Historical behaviour" records what changed.

## Endpoints

| Route | Method | Auth | Counts against quota |
|---|---|---|---|
| `/api/v1/search/vector` | POST | yes | yes |
| `/api/v1/search/semantic` | POST | yes | yes |
| `/api/v1/trends` | POST | yes | yes |
| `/api/subreddits` | GET | no | no |
| `/api/v1/subreddits` | GET | yes | yes |
| `/api/subreddits/<name>` | GET | no | no |
| `/api/v1/subreddits/<name>` | GET | yes | yes |

### POST /api/v1/search/vector

Nearest-neighbour search over the full archive.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `query` | string | required | empty or missing gives 400 |
| `limit` | number | 30 | max 100, higher values clamped not rejected |
| `start_date` | string | none | `YYYY-MM-DD`, genuinely applied |
| `end_date` | string | none | `YYYY-MM-DD` |

Fills the requested `limit` exactly. A 2026-01-01..2026-03-31 window returned
20 of 20 rows inside the range. Results carry `similarity_score` (0 to 1).

### POST /api/v1/search/semantic

Adds LLM keyword extraction on top of the same index, and caches per query for
roughly 12 hours.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `query` | string | required | |
| `limit` | number | 20 | max 100, reliably filled |
| `include_summary` | boolean | false | adds `data.ai_summary`, slow |

No date filter. Results carry `relevance` and `sentiment`. `sentiment` is
present in the schema but comes back empty on every result because the
classification step is disabled server-side.

### POST /api/v1/trends

Site-wide momentum. Not filterable by topic or subreddit.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `start_date` | string | today | always pass an explicit range |
| `end_date` | string | today | |
| `limit` | number | 20 | max 100 |

`GET` on this route returns 404 with an HTML body (no GET handler). A POST
with an empty body returns 500 because the body is parsed as JSON
unconditionally, so send at least `{}`.

### Subreddit routes

`/api/subreddits` takes `limit` (default 20, max 100), `page`, `search`.
`/api/v1/subreddits` adds `sort=subscribers|created`, `order=asc|desc`, an
`icon` field, and defaults `limit` to 50.

Detail routes return the same data under different keys: the public route
gives `recentPosts` (camelCase), the `/v1` route gives `recent_posts`
(snake_case). List responses use `data.subreddits[]` plus `total`, `page`,
`limit`, `total_pages`.

## Response shapes

Every endpoint wraps its payload in `data`. Read `response['data'][...]`,
never a top-level `results` or `trends` key.

### Search

```json
{
  "success": true,
  "data": {
    "query": "...",
    "results": [
      {
        "id": "post123",
        "title": "User post title",
        "content": "Post body text...",
        "subreddit": "somesub",
        "upvotes": 1234,
        "comments": 89,
        "created": "2026-01-15T10:30:00Z",
        "url": "https://reddit.com/r/somesub/comments/post123",
        "similarity_score": 0.87
      }
    ],
    "total": 30,
    "processing_time_ms": 340
  }
}
```

`total` is the count actually returned, not the size of the match set.

Field names are reddapi.dev's own. They do not match the official Reddit API:
`content` is not `selftext`, `upvotes` is not `score`, `comments` is not
`num_comments`, `created` is not `created_utc`.

### Trends

```json
{
  "success": true,
  "data": {
    "trends": [
      {
        "id": "trend001",
        "topic": "AI regulation",
        "post_count": 1247,
        "total_upvotes": 45632,
        "total_comments": 3120,
        "avg_sentiment": 0.42,
        "growth_rate": 245.3,
        "trend_score": 88.4,
        "top_subreddits": ["technology", "artificial"],
        "trending_keywords": ["regulation", "policy", "AI act"],
        "sample_posts": [
          {
            "id": "post123",
            "title": "Sample post title",
            "subreddit": "technology",
            "upvotes": 812,
            "comments": 143,
            "created": "2026-07-14T08:12:00.000Z"
          }
        ]
      }
    ],
    "total": 10,
    "date_range": { "start": "2026-07-01", "end": "2026-07-30" },
    "processing_time_ms": 210
  }
}
```

`sample_posts` holds full post objects, not bare ID strings.

## Status codes

| Code | Cause |
|---|---|
| 400 | missing or empty `query`, unparseable `start_date` / `end_date` |
| 403 | POST without `Content-Type: application/json`, not a plan limit |
| 404 | no handler for that method and path, e.g. `GET /api/v1/trends` |
| 429 | invalid or expired key, or plan quota exhausted |
| 500 | includes POSTing an empty body instead of JSON |

An invalid key returns 429, not 401. The monthly allowance is a shared pool:
web-app searches, API calls, and lead searches all draw from one counter.

## Historical behaviour

Before the 2026-07-31 server-side fix, vector search rehydrated every hit from
a roughly six-week rolling table and dropped the rest, so `limit: 100` came
back as about 50 and archive hits were unreachable. Notes written before that
date describe the old behaviour. Results now come straight from the vector
index metadata.
