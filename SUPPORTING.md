# Supporting Files

## Scripts

### reddapi-cli.sh
Command-line interface for reddapi.dev API. Requires `REDDAPI_API_KEY` in the
environment. Handles the `Content-Type` header, error hints, and trends' required
date range (defaults to the last 30 days) automatically.

```bash
./scripts/reddapi-cli.sh search "productivity tools" --limit 100
./scripts/reddapi-cli.sh search "productivity tools" --mode semantic --limit 20
./scripts/reddapi-cli.sh trends --start-date 2026-07-01 --end-date 2026-07-30
./scripts/reddapi-cli.sh subreddits --limit 50
./scripts/reddapi-cli.sh subreddit programming
```

## References

### api-examples.md
Real, timestamped request/response pairs captured against the live API - use to
verify a response shape or debug a mismatch. See that file's own "Verifying this
file still holds" section to re-capture if the API changes.

## Usage

See `skills/reddapi/SKILL.md` (or `skills/reddit-search-api/SKILL.md`, its
backward-compat alias) for complete documentation.
