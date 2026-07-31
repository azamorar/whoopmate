<div align="center">

# 🏋️ WHOOP MCP Server

**Bring your WHOOP health data into any MCP-compatible AI assistant.**

A local [Model Context Protocol](https://modelcontextprotocol.io) server that exposes your [WHOOP](https://www.whoop.com) recovery, sleep, strain, and workout data as tools your AI can call — built with [FastMCP](https://gofastmcp.com) and running locally over stdio.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org)
[![FastMCP](https://img.shields.io/badge/built%20with-FastMCP-6f42c1.svg)](https://gofastmcp.com)
[![MCP](https://img.shields.io/badge/protocol-MCP-000000.svg)](https://modelcontextprotocol.io)
[![WHOOP API](https://img.shields.io/badge/WHOOP%20API-v2-orange.svg)](https://developer.whoop.com/api)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

</div>

---

## Overview

`whoop-mcp` connects your personal WHOOP account to AI assistants like **Claude Desktop** and **Claude Code**. Once authorized, you can ask your assistant natural-language questions about your health:

> *"How did I recover last week?"*
> *"Compare my sleep on days I worked out vs. rest days."*
> *"What was my highest-strain workout this month?"*

The server handles OAuth2 authentication, automatic token refresh, and pagination — you just log in once and start asking questions.

## Features

- 🔐 **OAuth2 with automatic refresh** — authorize once; the server rotates and refreshes tokens transparently.
- 📊 **11 tools across 5 domains** — profile, physiological cycles, recovery, sleep, and workouts.
- 🗓️ **Flexible date filtering** — every collection accepts `YYYY-MM-DD` or full ISO 8601 timestamps.
- 📄 **Built-in pagination** — cursor-based paging through your full history.
- 🧩 **Clean, modular codebase** — one module per WHOOP domain, easy to extend.
- 🔒 **Local-first** — runs on your machine over stdio; your tokens never leave `~/.whoop-mcp/`.

## Available Tools

| Tool | Description |
|------|-------------|
| `get_profile` | Basic profile (name, email, user ID) |
| `get_body_measurements` | Height, weight, and max heart rate |
| `get_cycles` | Physiological cycles (daily strain), paginated |
| `get_cycle_by_id` | A single cycle by ID |
| `get_recoveries` | Recovery records (score, HRV, RHR, SpO₂), paginated |
| `get_latest_recovery` | Your most recent recovery |
| `get_cycle_recovery` | Recovery for a specific cycle |
| `get_sleeps` | Sleep sessions (stages, efficiency), paginated |
| `get_sleep_by_id` | A single sleep session by ID |
| `get_workouts` | Workouts (sport, strain, HR zones), paginated |
| `get_workout_by_id` | A single workout by ID |

Paginated tools accept `limit` (max 25), `start`/`end` dates, and `next_token` to continue paging.

## Project Structure

```
whoop-mcp/
├── pyproject.toml          # Dependencies & scripts (Poetry)
├── .env.example            # Credentials template
└── src/whoop_mcp/
    ├── server.py           # Entry point: builds FastMCP, registers tools
    ├── config.py           # Configuration (env vars, URLs, scopes)
    ├── auth.py             # OAuth2 token management (storage + auto-refresh)
    ├── auth_cli.py         # Browser-based OAuth2 login flow
    ├── client.py           # Async HTTP client (httpx) with 401 retry
    └── tools/              # MCP tools grouped by domain
        ├── profile.py
        ├── cycles.py
        ├── recovery.py
        ├── sleep.py
        └── workouts.py
```

## Prerequisites

1. A [WHOOP Developer](https://developer.whoop.com) account with an application created.
2. In your app settings, register the redirect URI: `http://localhost:8765/callback`.
3. Enable these scopes: `read:profile`, `read:body_measurement`, `read:cycles`, `read:recovery`, `read:sleep`, `read:workout`, `offline`.

## Installation

```bash
poetry install
cp .env.example .env   # then fill in WHOOP_CLIENT_ID / WHOOP_CLIENT_SECRET
```

## Authorization (one time)

```bash
poetry run python -m whoop_mcp.auth_cli
```

Your browser opens, you log in to WHOOP, and tokens are saved to `~/.whoop-mcp/tokens.json`. The server refreshes the access token automatically from then on (WHOOP rotates the refresh token on each refresh, and the server persists the new one).

## Running the Server

```bash
poetry run python -m whoop_mcp
```

The server speaks MCP over stdio — normally your MCP client launches it, not you.

> **Note:** We use `python -m whoop_mcp` instead of the `whoop-mcp` console script because, if the project lives in a path containing spaces (e.g. iCloud Drive), the entry-point shebang breaks with `bad interpreter`. The `python -m` form always works.

## Configuring Claude Desktop / Claude Code

Get the venv's Python path:

```bash
echo "$(poetry env info --path)/bin/python"
```

Add it to your MCP client config (`claude_desktop_config.json` or `.mcp.json`):

```json
{
  "mcpServers": {
    "whoop": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "whoop_mcp"]
    }
  }
}
```

In Claude Code you can also run:

```bash
claude mcp add whoop -- "<venv-path>/bin/python" -m whoop_mcp
```

## Development

Test the server interactively with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector poetry run python -m whoop_mcp
```

## API Reference

This server is built against the **WHOOP API v2**. Official documentation:

- 📖 **WHOOP Developer Docs** — https://developer.whoop.com
- 📚 **API Reference** — https://developer.whoop.com/api
- 🔑 **OAuth 2.0 Guide** — https://developer.whoop.com/docs/developing/oauth

## Roadmap

See [`NEXT_STEPS.md`](./NEXT_STEPS.md) for planned features, including higher-level analytical tools (weekly recovery summaries, sleep-vs-workout comparisons, strain aggregates by sport, and combined daily reports).

## License

Released under the MIT License. WHOOP is a trademark of WHOOP, Inc.; this project is an independent client and is not affiliated with or endorsed by WHOOP, Inc.
