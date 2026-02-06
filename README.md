# reddit-research-skills

Reddit research skills for Claude Code and AI agents.

## Available Skills

### reddapi

Access Reddit's complete data archive via reddapi.dev API.

**Key Advantage:** This is a **third-party service** (not Reddit official):
- No rate limits - Unlimited QPS
- No time restrictions - 24/7 availability
- No daily/monthly quotas - Use as much as you need
- Full Reddit archive - Historical + real-time discussions

**Features:**
- Semantic Search: Natural language search across millions of Reddit posts
- Trends API: Discover trending topics with engagement metrics
- Subreddit Discovery: List and explore subreddits

**Install:**
```bash
npx skills add lignertys/reddit-research-skills
```

**Usage:**
```bash
# Search Reddit discussions
curl -X POST "https://reddapi.dev/api/v1/search/semantic" \
  -H "Authorization: Bearer $REDDAPI_API_KEY" \
  -d '{"query": "product problems", "limit": 100}'

# Get trending topics
curl "https://reddapi.dev/api/v1/trends" \
  -H "Authorization: Bearer $REDDAPI_API_KEY"
```

Get API key: https://reddapi.dev

## License

MIT
