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

**Usage in Conversation:**

After installing the skill, simply ask in natural language:

```markdown
Find discussions about iPhone problems and complaints on Reddit

Search for user frustrations with current productivity tools

What are people saying about AI agent limitations?

Find Reddit discussions about competitor pain points for TOOL_NAME

Analyze trends in remote work discussions
```

The skill will use reddapi.dev to search Reddit and return relevant discussions with engagement metrics.

**Get API Key:**
https://reddapi.dev

## License

MIT
