# reddit-research-skills

Reddit research skills for Claude Code and AI agents.

## Available Skills

### reddit-research (canonical)

Market research, user research, and product validation on Reddit via
reddapi.dev - semantic search across 50K+ subreddits, 20M+ posts, and 40M+
comments, trends over a date range, and subreddit discovery, plus query
playbooks for competitor research, niche validation, and trend tracking.

### reddapi (legacy name)

The original skill name for the same engine as `reddit-research`, kept live
for existing installs. Fully functional standalone; new installs should
prefer `reddit-research` for the expanded playbooks.

### reddit-search-api (reference)

Pure API reference for the same engine - endpoints, parameters, response
schemas, error codes, no research-workflow framing. For developers who just
want the API docs.

### reddit-leads

B2B lead discovery - finds Reddit posts with buying intent, scores them 0-100, and
classifies by lead type (pain_point, solution_request, complaint, feature_request,
comparison). Requires a paid reddapi.dev plan.

**Key facts:** This is a **third-party service** (not Reddit official) - no Reddit
OAuth or app registration needed. It is **not** unlimited: access is gated by
plan-based rate limits (see `skills/reddit-leads/SKILL.md` for the plan/quota table);
an invalid or exhausted key returns HTTP 429.

**Features:**
- Semantic Search (default): natural-language search over the full archive, exact
  result counts up to `limit: 100`, LLM keyword extraction and an optional AI
  summary; no date filter
- Vector Search: same archive with `similarity_score` and working date filters -
  the mode to use when a question is scoped to a date range
- Trends API: named entities Reddit is talking about in a date window, with growth vs the previous window
- Subreddit Discovery: list and look up subreddits

**Install:**
```bash
npx skills add https://github.com/lignertys/reddit-research-skills --skill reddit-research
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
