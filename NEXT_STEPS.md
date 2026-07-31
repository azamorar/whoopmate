# Next Steps & Project Context

> This document captures the current state of `whoop-mcp` and planned work, so a
> new conversation (or a new contributor) can pick up without re-deriving anything.

## Current State (as of 2026-07-16)

The MCP server is **complete, installed, and verified end-to-end over stdio**. It
starts, exposes **11 tools**, and returns clear errors when configuration is
missing.

- **Framework:** FastMCP 2.14.7 (Python), transport: **stdio**.
- **Dependency manager:** Poetry. Virtualenv lives in `.venv/` inside the project.
- **Python:** 3.11.
- **WHOOP API:** v2 (base URL `https://api.prod.whoop.com/developer`).
- **HTTP client:** `requests` (synchronous). Tools are plain `def` (not `async`);
  FastMCP runs sync tools in a worker thread, so blocking calls don't stall the
  event loop. `httpx` is still present transitively (FastMCP depends on it) but
  our code does not import it — don't reintroduce it.

### What works today

- OAuth2 authorization code flow via a local callback server (`auth_cli.py`).
- Token storage in `~/.whoop-mcp/tokens.json` (mode `0600`).
- Automatic access-token refresh with refresh-token rotation (WHOOP rotates the
  refresh token on every refresh; the server persists the new one).
- Automatic single retry on `401` (force-refresh + retry).
- Cursor-based pagination on all collection endpoints.
- Lazy client initialization — the server boots even without `.env`, and the
  config error only surfaces when a tool is actually called.

### The 11 tools

| Domain | Tools |
|--------|-------|
| Profile | `get_profile`, `get_body_measurements` |
| Cycles | `get_cycles`, `get_cycle_by_id` |
| Recovery | `get_recoveries`, `get_latest_recovery`, `get_cycle_recovery` |
| Sleep | `get_sleeps`, `get_sleep_by_id` |
| Workouts | `get_workouts`, `get_workout_by_id` |

## ⚠️ Critical Gotcha — iCloud path / spaces

The project lives in **iCloud Drive** (`~/Library/Mobile Documents/...`), a path
that **contains spaces**. This breaks Poetry's console-script entry points
(`.venv/bin/whoop-mcp`, `.venv/bin/whoop-auth`) with a `bad interpreter` error,
because the script's shebang line does not tolerate spaces in the path.

**Always launch via `python -m`:**

- Server: `poetry run python -m whoop_mcp`
- Auth:   `poetry run python -m whoop_mcp.auth_cli`
- Direct: `<venv>/bin/python -m whoop_mcp`

`src/whoop_mcp/__main__.py` exists specifically to support this. Do **not**
tell users to run the bare `whoop-mcp` / `whoop-auth` scripts.

## Setup Checklist (for the user, not yet done)

1. Create an app in the [WHOOP Developer Dashboard](https://developer.whoop.com):
   - Redirect URI: `http://localhost:8765/callback`
   - Scopes: `read:profile`, `read:body_measurement`, `read:cycles`,
     `read:recovery`, `read:sleep`, `read:workout`, `offline`
2. `cp .env.example .env` and fill in `WHOOP_CLIENT_ID` / `WHOOP_CLIENT_SECRET`.
3. Authorize once: `poetry run python -m whoop_mcp.auth_cli`.
4. Register in the MCP client (see README → "Configuring Claude Desktop / Claude Code").
5. **Test with real data** — none of the tools have been exercised against a live
   WHOOP account yet, only against the missing-credentials error path.

## Planned Features (higher-level analytical tools)

These build on the existing raw-data tools by aggregating and combining results.
Each should live in its own module under `src/whoop_mcp/tools/` (e.g.
`analytics.py`) and be registered in `tools/__init__.py`.

### 1. Weekly recovery summary
- **Tool:** `get_recovery_summary(days: int = 7)`
- Aggregate recovery score / HRV / RHR over a window: min, max, mean, trend.
- Flag notable days (e.g. recovery < 33% "red", > 66% "green").

### 2. Sleep vs. workout comparison
- **Tool:** `compare_sleep_by_activity(days: int = 14)`
- Join sleep sessions with workouts by date; compare sleep performance /
  efficiency on workout days vs. rest days.

### 3. Strain aggregates by sport
- **Tool:** `get_strain_by_sport(start, end)`
- Group workouts by `sport_id`, sum/avg strain, kilojoules, and duration.
- May need a `sport_id → name` lookup table (WHOOP publishes sport IDs).

### 4. Combined daily report
- **Tool:** `get_daily_report(date: str)`
- One call that stitches together the cycle (strain), recovery, and sleep for a
  given day into a single structured summary.

### 5. Trend detection (stretch)
- **Tool:** `detect_trends(metric, days)`
- Simple linear trend / week-over-week deltas for a chosen metric.

## Implementation Notes for Future Work

- **Reuse the client.** All tools receive the shared `WhoopClient` instance via
  `register(mcp, client)`. Analytical tools should call `client.get_collection(...)`
  and aggregate in Python — don't add new HTTP plumbing. New tools are sync `def`
  (see the HTTP-client note under "Current State").
- **Date helper.** `client.to_iso_datetime()` converts `YYYY-MM-DD` or ISO 8601 to
  the full ISO timestamp WHOOP requires. Reuse it.
- **Pagination.** For multi-page aggregates, loop on the `next_token` field of the
  response until it's absent. Consider a helper like
  `client.get_all(path, start, end)` that pages through everything (respect the
  25-record page cap and rate limits — WHOOP returns `429` when throttled).
- **WHOOP data shapes.** Recovery/sleep/workout scores live under a `score` object
  in each record; `score_state` may be `SCORED`, `PENDING_SCORE`, or
  `UNSCORABLE` — handle non-scored records gracefully in aggregates.
- **Testing.** There are no automated tests yet. A good first addition:
  `pytest` + `responses` (or `requests-mock`) to test `client.py` retry/refresh
  logic and the aggregation math without hitting the real API.

## Useful References

- WHOOP Developer Docs: https://developer.whoop.com
- WHOOP API Reference (v2): https://developer.whoop.com/api
- WHOOP OAuth 2.0 Guide: https://developer.whoop.com/docs/developing/oauth
- FastMCP Docs: https://gofastmcp.com
- MCP Spec: https://modelcontextprotocol.io
