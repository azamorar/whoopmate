<div align="center">

# 🏋️ WHOOP MCP Server

**Bring your WHOOP health data into any MCP-compatible AI assistant.**

A local [Model Context Protocol](https://modelcontextprotocol.io) server that gives your AI assistant access to your [WHOOP](https://www.whoop.com) recovery, sleep, strain, and workout data. Built with [FastMCP](https://gofastmcp.com), runs entirely on your machine.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org)
[![FastMCP](https://img.shields.io/badge/built%20with-FastMCP-6f42c1.svg)](https://gofastmcp.com)
[![MCP](https://img.shields.io/badge/protocol-MCP-000000.svg)](https://modelcontextprotocol.io)
[![WHOOP API](https://img.shields.io/badge/WHOOP%20API-v2-orange.svg)](https://developer.whoop.com/api)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#license)

</div>

---

## What it does

Connect this server to Claude Desktop or Claude Code, and ask your WHOOP data questions in plain language:

> *"How did I recover last week?"*
> *"Compare my sleep on days I worked out vs. rest days."*
> *"What was my highest-strain workout this month?"*

Everything runs locally. Your data never touches a third-party server, and only you can access it.

## Setup

**1. Create a WHOOP app.** Go to the [WHOOP Developer Dashboard](https://developer.whoop.com) and create a new app. You'll need this because WHOOP requires every integration to authenticate with its own credentials (see [Why your own app?](#why-your-own-app) below).

- Redirect URI: `http://localhost:8007/callback`
- Scopes: `read:profile`, `read:body_measurement`, `read:cycles`, `read:recovery`, `read:sleep`, `read:workout`, `offline`

**2. Install.**

```bash
git clone https://github.com/azamorar/whoopmate.git
cd whoopmate
poetry install
cp .env.example .env
```

Open `.env` and fill in the `WHOOP_CLIENT_ID` and `WHOOP_CLIENT_SECRET` from your app.

**3. Connect it to your AI assistant.** Get the path to the Python interpreter inside the project's virtual environment:

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

Or, in Claude Code:

```bash
claude mcp add whoop -- "<venv-path>/bin/python" -m whoop_mcp
```

**4. Log in.** The first time your assistant needs your WHOOP data, it opens your browser to WHOOP's login page. Log in once, and you're done. Nothing to run by hand.

## Available tools

| Tool | What it does |
|------|------|
| `whoop_login` | Authorizes access to your WHOOP account. Runs on its own when needed. |
| `whoop_auth_status` | Checks whether you're logged in already. |
| `get_profile` | Your basic profile (name, email, user ID) |
| `get_body_measurements` | Height, weight, and max heart rate |
| `get_cycles` | Daily strain cycles, with pagination |
| `get_cycle_by_id` | One specific cycle |
| `get_recoveries` | Recovery scores, HRV, resting heart rate, with pagination |
| `get_latest_recovery` | Your most recent recovery |
| `get_cycle_recovery` | Recovery for a specific cycle |
| `get_sleeps` | Sleep sessions with stages and efficiency, with pagination |
| `get_sleep_by_id` | One specific sleep session |
| `get_workouts` | Workouts with strain and heart rate zones, with pagination |
| `get_workout_by_id` | One specific workout |

Paginated tools accept `limit` (up to 25), `start`/`end` dates (`YYYY-MM-DD` works fine), and `next_token` to keep paging.

## How login works

You never run a login command yourself. The first time a tool needs your WHOOP data and you're not logged in, it opens your browser to WHOOP's login page and waits for you to finish. From then on, the server renews your access in the background on its own. Revoke access from your WHOOP account, and you'll be asked to log in again next time you use it.

Tokens are stored in `~/.whoop-mcp/tokens.json` on your machine, never anywhere else.

If you'd rather log in ahead of time from a terminal, that works too:

```bash
poetry run python -m whoop_mcp.auth_cli
```

## Why your own app?

This project doesn't ship with shared WHOOP credentials, and never will. Everyone who runs it creates their own free app on the WHOOP Developer Dashboard.

An app's `client_id`/`client_secret` identify the app itself. Your `access_token` identifies your account, and you get it by logging in yourself. Keeping those two things separate means nobody's credentials or health data ever have to cross machines. There's no shared secret and no central server to trust, because WHOOP's API only supports OAuth2 logins.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Missing WHOOP_CLIENT_ID and/or WHOOP_CLIENT_SECRET" | Fill in `.env` with your app's credentials, then restart the server. |
| "No authorized WHOOP session yet" | Nothing to do: the assistant opens your browser and logs you in. |
| `invalid_scope` during login | Enable all the required scopes for your app in the Developer Dashboard. |
| `redirect_uri` mismatch during login | The URI in `.env` must match the Developer Dashboard exactly, including the port. |
| `bad interpreter` running the server | Happens if the project path has spaces in it (like iCloud Drive). Use `python -m whoop_mcp` instead of the `whoop-mcp` shortcut. |

## Testing with MCP Inspector

Before wiring this into your AI assistant, you can poke at it directly:

```bash
npx @modelcontextprotocol/inspector poetry run python -m whoop_mcp
```

This opens a browser tab where you can run any tool by hand and see the raw response.

## API reference

Built against the WHOOP API v2:

- [Developer Docs](https://developer.whoop.com)
- [API Reference](https://developer.whoop.com/api)
- [OAuth 2.0 Guide](https://developer.whoop.com/docs/developing/oauth)

## License

MIT. WHOOP is a trademark of WHOOP, Inc. This project is an independent client, not affiliated with or endorsed by WHOOP, Inc.
