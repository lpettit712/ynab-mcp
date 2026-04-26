# YNAB MCP

Read-only FastMCP server for talking to your YNAB budget from an MCP-capable assistant.

This project is not affiliated with, associated with, or officially connected with YNAB or any of its subsidiaries or affiliates. The official YNAB website is https://www.ynab.com.

## Features

- List YNAB plans, accounts, categories, transactions, and payees.
- Get a daily check-in with account balances, category risk, and recent transactions.
- Analyze current-month spending by category or payee.
- Show largest transactions for a date window.
- Uses read-only MCP tools. It does not create, update, delete, approve, import, or categorize transactions.

## Setup

Install dependencies:

```bash
uv sync
```

Create a YNAB Personal Access Token from YNAB Developer Settings, then export it before running the server:

```bash
export YNAB_ACCESS_TOKEN="your-real-token"
```

Do not commit real tokens. `.env` is ignored by git, and `.env.example` contains a placeholder only.

## Run

Run with the default stdio transport:

```bash
uv run fastmcp run src/ynab_mcp/server.py:mcp
```

Run over HTTP for local testing:

```bash
uv run fastmcp run src/ynab_mcp/server.py:mcp --transport http --port 8000
```

## Tools

- `list_plans`
- `get_plan_summary`
- `list_accounts`
- `list_categories`
- `list_transactions`
- `list_payees`
- `daily_checkin`
- `spending_by_category`
- `spending_by_payee`
- `largest_transactions`

## Tests

Tests use mocked YNAB responses and do not require a real token:

```bash
uv run pytest
```
