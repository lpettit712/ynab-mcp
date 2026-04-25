# YNAB MCP Design

Date: 2026-04-25

## Goal

Build a simple local FastMCP server that lets an MCP-capable assistant answer read-only questions about a user's YNAB plan. The first version focuses on daily check-ins and spending analysis, using the user's own YNAB Personal Access Token.

## Non-Goals

- No write actions: no creating, updating, deleting, approving, importing, or categorizing transactions.
- No OAuth or multi-user account flow.
- No committed secrets, generated token files, or persisted YNAB credentials.
- No UI or hosted deployment in the first version.

## Architecture

The project will be a small Python package using FastMCP v3. It will run over stdio by default for local MCP clients, with an optional HTTP run command for local testing.

Modules:

- `server.py`: creates the FastMCP app and registers tools.
- `config.py`: loads and validates environment configuration.
- `ynab_client.py`: calls `https://api.ynab.com/v1` with the configured token.
- `models.py`: defines concise internal types for normalized YNAB data.
- `summaries.py`: computes daily check-ins and spending analysis from normalized data.

Keep code concise: prefer small functions and direct data transformations over broad abstraction layers.

## Authentication And Secrets

The server reads `YNAB_ACCESS_TOKEN` from the environment. If the variable is missing, tools fail with a clear configuration message.

Repository rules:

- Commit `.env.example` with `YNAB_ACCESS_TOKEN=your-token-here`.
- Commit `.gitignore` entries for `.env`, virtual environments, Python caches, coverage output, and local test artifacts.
- Never log or persist the token.
- Never commit real tokens.

## MCP Tool Surface

Raw read tools:

- `list_plans()`: list available YNAB plans.
- `get_plan_summary(plan_id="default")`: fetch high-level plan metadata.
- `list_accounts(plan_id="default")`: account names, types, balances, closed status, and on-budget status.
- `list_categories(plan_id="default", month="current")`: category groups and category balances for the selected month.
- `list_transactions(plan_id="default", start_date=None, end_date=None, limit=100)`: recent or date-filtered transactions.
- `list_payees(plan_id="default")`: payee lookup support.

Summary tools:

- `daily_checkin(plan_id="default")`: account balances, overspent or negative categories, low category balances, and recent transactions.
- `spending_by_category(plan_id="default", start_date=None, end_date=None)`: grouped spending by category.
- `spending_by_payee(plan_id="default", start_date=None, end_date=None)`: grouped spending by payee.
- `largest_transactions(plan_id="default", start_date=None, end_date=None, limit=10)`: largest outflows in the selected window.

Tool outputs should be concise JSON-style dictionaries. Use formatted amount fields from YNAB when present, and convert milliunits as a fallback.

## Defaults

- `plan_id` defaults to `"default"`.
- Analysis date windows default to the current calendar month.
- Transaction outputs default to `limit=100`.
- Summary tools omit inactive data unless it affects the answer, such as a negative category balance.
- Raw tools expose the underlying read data needed for debugging and flexible assistant use.

## Data Flow

1. MCP client calls a FastMCP tool.
2. Tool validates arguments and resolves defaults.
3. Tool calls `ynab_client.py`.
4. The YNAB client sends an authenticated HTTPS request to `https://api.ynab.com/v1`.
5. The response is unwrapped from YNAB's standard `{ "data": ... }` envelope.
6. Raw tools return normalized data directly.
7. Summary tools pass normalized data through `summaries.py` before returning.

## Error Handling

- Missing `YNAB_ACCESS_TOKEN`: return a configuration error with the expected environment variable name.
- 401 or 403 from YNAB: return an authentication or permission error without exposing secrets.
- 404 from YNAB: explain that the requested plan or resource was not found.
- 429 from YNAB: explain that the YNAB rate limit was hit and the user should wait before retrying.
- Other YNAB errors: include status code and YNAB error detail when present.
- Network errors: return a concise connectivity error.

## Testing

Tests use mocked YNAB responses and must not require a real YNAB token.

Coverage:

- Config validation for missing and present token values.
- YNAB client request paths, authorization header setup, response envelope handling, and error mapping.
- Summary helpers for current-month defaulting, category/payee grouping, largest transaction sorting, and negative category detection.
- MCP tool smoke tests using mocked client data.

## Setup Documentation

The README will include:

- How to install dependencies with `uv`.
- How to set `YNAB_ACCESS_TOKEN` locally.
- How to run the server with stdio.
- How to run it over HTTP for local testing.
- How to run tests.
- A short security note that real tokens must never be committed.

## External References

- FastMCP docs: https://gofastmcp.com/getting-started/welcome
- FastMCP quickstart: https://gofastmcp.com/getting-started/quickstart
- YNAB API docs: https://api.ynab.com/
