---
name: reddit-leads
description: Discover B2B leads from Reddit using AI-powered lead scoring via reddapi.dev Leads API. Finds high-intent signals, scores them 0-100, and classifies by lead type (pain_point, solution_request, complaint, feature_request, comparison). Perfect for competitor poaching, pain point discovery, and sales prospecting.
license: MIT
keywords:
  - reddit
  - leads
  - b2b
  - lead-generation
  - prospecting
  - competitor-intelligence
  - sales
---

# reddit-leads Skill

## Overview

AI-powered B2B lead discovery from Reddit. Finds users actively expressing buying intent, scores them 0-100, and classifies by lead type — so you can focus on the warmest prospects first.

**Powered by [reddapi.dev](https://reddapi.dev/leads)** — The Lead Engine indexes 50K+ subreddits with 1.5M+ posts, using 1024D vector search to match on meaning, not just keywords.

**Key Advantage:**
- ✅ **AI lead scoring** — Every post scored 0-100 on buying intent signal strength
- ✅ **5 lead type categories** — pain_point, solution_request, complaint, feature_request, comparison
- ✅ **Industry inference** — AI auto-detects industry/context from discussion content
- ✅ **Zero noise** — Filters out support tickets, memes, and irrelevant mentions
- ✅ **Competitor intelligence** — Find users actively complaining about or switching from competitors

## Setup

### Get API Key
1. Create an account at https://reddapi.dev
2. Subscribe to a paid plan (Free: 3 searches/mo, Lite $19.9/mo, Starter $49/mo, Pro $99/mo)
3. Go to https://reddapi.dev/account to view or generate your API key

### Environment Variable
```bash
export REDDAPI_API_KEY="your_api_key_here"
```

### Rate Limits

| Plan | Monthly API Calls | Per Minute |
|------|-------------------|------------|
| Free | 3 | — |
| Lite | 500 | 50 |
| Starter | 5,000 | 50 |
| Pro | 15,000 | 100 |
| Enterprise | Unlimited | 1,000 |

## API Reference

**Base URL:** `https://reddapi.dev`

**Authentication:** All requests require header:
```
Authorization: Bearer YOUR_API_KEY
```

### POST /api/v1/leads

Find scored, classified business leads from Reddit discussions.

```bash
curl -X POST "https://reddapi.dev/api/v1/leads" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "people frustrated with project management tools", "limit": 20, "min_score": 60}'
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Natural language lead query — describe who you're looking for |
| limit | number | No | Results to return (default: 20, max: 100) |
| min_score | number | No | Minimum lead score filter (0-100, default: 0) |

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "people frustrated with project management tools",
    "results": [
      {
        "id": "lead001",
        "title": "Asana is getting too expensive for our team of 15",
        "content": "We're paying $400/mo for Asana and half our team doesn't even use it...",
        "subreddit": "projectmanagement",
        "author": "pm_burnt_out",
        "upvotes": 234,
        "comments": 89,
        "lead_score": 94,
        "lead_type": "pain_point",
        "pain_point": "Pricing - cost too high for team size",
        "opportunity": "Affordable project management alternative for mid-size teams",
        "industry": "SaaS / Project Management",
        "target_product": "Asana",
        "url": "https://reddit.com/r/projectmanagement/comments/lead001"
      }
    ],
    "total": 2,
    "processing_time_ms": 840
  }
}
```

### Lead Types (5 Categories)

| Type | Description | Example |
|------|-------------|---------|
| `pain_point` | Users frustrated with current solutions | "Jira is so slow and bloated" |
| `solution_request` | Users actively asking for alternatives | "What's a good alternative to X?" |
| `complaint` | Users complaining about specific products | "Salesforce support is terrible" |
| `feature_request` | Users requesting missing features | "I wish Notion had calendar views" |
| `comparison` | Users comparing products/options | "Trying to decide between HubSpot and Pipedrive" |

### Lead Score (0-100)

AI evaluates each post on:
- **Signal strength** — How clearly the user expresses a need
- **Buying intent** — How likely they are to take action
- **Relevance** — How well it matches the query
- **Engagement** — Upvotes and comments as validation signals

| Score Range | Meaning | Action |
|-------------|---------|--------|
| 90-100 | 🔥 Hot lead — explicit buying intent | Reach out immediately |
| 70-89 | 🟡 Warm lead — strong frustration/need | Engage with helpful content |
| 50-69 | 🟠 Moderate — mild interest or tangential | Monitor and nurture |
| 0-49 | ❌ Cold — low signal, skip | Ignore |

**Recommendation:** Use `min_score: 60` to filter out noise. Use `min_score: 80` for only the hottest leads.

## Query Strategies

### Competitor Switching (Highest Score)
Find users actively looking to leave a competitor:
```
"founders looking to switch from [competitor]"
→ Expected Score: 90-98
→ Types: solution_request, comparison

"SaaS founders complaining about Stripe fees"
→ Expected Score: 92-98
→ Types: complaint, pain_point

"people migrating away from [product] alternatives"
→ Expected Score: 85-96
→ Types: solution_request, comparison
```

### Pain Point Discovery
Find users frustrated with current tools:
```
"frustrated with CRM software small business"
→ Expected Score: 80-95
→ Types: pain_point, complaint

"tired of paying too much for email marketing"
→ Expected Score: 75-92
→ Types: pain_point, complaint

"my current tool is broken and I need alternatives"
→ Expected Score: 80-94
→ Types: solution_request, pain_point
```

### Feature Gap Targeting
Find users asking for features you provide:
```
"need a tool that does X but simpler"
→ Expected Score: 70-90
→ Types: feature_request, solution_request

"wish there was a product for Y"
→ Expected Score: 75-92
→ Types: feature_request, solution_request
```

### Niche Industry Targeting
Find leads in specific industries:
```
"restaurants struggling with online ordering"
→ Expected Score: 78-94
→ Types: pain_point, solution_request

"dentists looking for patient scheduling software"
→ Expected Score: 82-96
→ Types: solution_request, comparison
```

### Quick Reference: Query → Score Patterns

| Query Pattern | Score | Best For |
|--------------|-------|----------|
| "people frustrated with [category]" | 80-98 | General pain points |
| "[audience] looking for [solution] alternative" | 75-95 | Switcher targeting |
| "switching from [competitor] to" | 90-98 | Competitor poaching |
| "[competitor] too expensive" | 85-96 | Price-based positioning |
| "wish [product] could" | 70-90 | Feature gap targeting |
| "[industry] need help with [problem]" | 75-94 | Industry targeting |
| "best alternative to [product]" | 85-96 | Direct competitor targeting |

## Example Workflows

### Competitor Lead Mining
```bash
# Find people ready to switch from your competitor
curl -X POST "https://reddapi.dev/api/v1/leads" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "founders looking to switch from Stripe alternatives", "limit": 20, "min_score": 80}'
```

### Price-Sensitive Prospects
```bash
# Find users complaining about pricing
curl -X POST "https://reddapi.dev/api/v1/leads" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "SaaS tool too expensive looking for cheaper alternative", "limit": 30, "min_score": 70}'
```

### Feature-Based Targeting
```bash
# Find users asking for features you offer
curl -X POST "https://reddapi.dev/api/v1/leads" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "project management tool with AI features", "limit": 20, "min_score": 60}'
```

### Multi-Competitor Sweep
```bash
# Run leads queries for multiple competitors
for competitor in "Asana" "Monday" "ClickUp" "Trello"; do
  echo "=== Leads for: $competator ==="
  curl -s -X POST "https://reddapi.dev/api/v1/leads" \
    -H "Authorization: Bearer YOUR_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"looking for alternatives to $competitor\", \"limit\": 10, \"min_score\": 70}"
done
```

## Tips

1. **Be specific about the audience** — "small business owners frustrated with X" beats "frustrated with X"
2. **Use competitor names** — Direct competitor mentions score highest (90+)
3. **Set min_score to 60+** — Filter out low-signal matches
4. **Run multiple queries** — Different phrasing catches different leads
5. **Combine with semantic search** — Use leads for high-intent prospects, then semantic search for broader context
6. **Monitor regularly** — New leads appear daily; set up recurring queries
7. **Lead type matters** — `solution_request` and `comparison` types indicate active buying consideration
8. **Check engagement metrics** — High upvotes/comments = validated pain point

## Integrating with Outreach

Once you have leads, here's how to use them:

1. **Hot leads (90+)**: Direct, personalized outreach referencing their specific Reddit post
2. **Warm leads (70-89)**: Create content addressing their pain point, then share
3. **Moderate (50-69)**: Add to nurture sequences, monitor for score increases

### CRM Export Format
Each lead result includes:
- `author` — Reddit username
- `subreddit` — Where they posted
- `url` — Direct link to the discussion
- `lead_score` — Priority ranking
- `lead_type` — Outreach approach guidance
- `industry` — Segmentation
- `target_product` — What they're using/complaining about
- `pain_point` / `opportunity` — Messaging hooks

## Error Handling

All endpoints return consistent error responses:
```json
{
  "success": false,
  "error": "Error description",
  "message": {
    "title": "Human-readable title",
    "message": "Detailed explanation",
    "cta": "Suggested action",
    "ctaLink": "/pricing"
  }
}
```

Common status codes: `400` (invalid params), `401` (bad API key), `403` (plan limit), `429` (rate limit), `500` (server error)
