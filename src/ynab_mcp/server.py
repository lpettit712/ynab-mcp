from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from fastmcp import FastMCP

from ynab_mcp.config import SettingsError
from ynab_mcp.summaries import current_month
from ynab_mcp.ynab_client import YnabApiError, YnabClient


mcp = FastMCP("YNAB MCP")


def _client() -> YnabClient:
    return YnabClient.from_env()


def _tool_call(fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except SettingsError as exc:
        return {"error": {"type": "configuration", "message": str(exc)}}
    except YnabApiError as exc:
        return {
            "error": {
                "type": exc.error_type,
                "status_code": exc.status_code,
                "message": exc.message,
            }
        }


def _current_month_window(today: date | None = None) -> tuple[str, str]:
    value = today or date.today()
    return value.replace(day=1).isoformat(), value.isoformat()


def _resolve_month(month: str) -> str:
    return current_month() if month == "current" else month


def _resolve_dates(start_date: str | None, end_date: str | None) -> tuple[str, str]:
    if start_date and end_date:
        return start_date, end_date
    default_start, default_end = _current_month_window()
    return start_date or default_start, end_date or default_end


@mcp.tool
def list_plans() -> dict[str, Any]:
    """List YNAB plans available to the configured token."""

    def run() -> dict[str, Any]:
        with _client() as client:
            return {"plans": client.list_plans()}

    return _tool_call(run)


@mcp.tool
def get_plan_summary(plan_id: str = "default") -> dict[str, Any]:
    """Fetch high-level metadata for a YNAB plan."""

    def run() -> dict[str, Any]:
        with _client() as client:
            return {"plan": client.get_plan_summary(plan_id)}

    return _tool_call(run)


@mcp.tool
def list_accounts(plan_id: str = "default") -> dict[str, Any]:
    """List accounts for a YNAB plan."""

    def run() -> dict[str, Any]:
        with _client() as client:
            return {"accounts": client.list_accounts(plan_id)}

    return _tool_call(run)


@mcp.tool
def list_categories(plan_id: str = "default", month: str = "current") -> dict[str, Any]:
    """List categories and balances for a YNAB plan month."""

    def run() -> dict[str, Any]:
        with _client() as client:
            return {"categories": client.list_categories(plan_id, _resolve_month(month))}

    return _tool_call(run)


@mcp.tool
def list_transactions(
    plan_id: str = "default",
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """List transactions for a YNAB plan, defaulting to the current month."""

    def run() -> dict[str, Any]:
        resolved_start, resolved_end = _resolve_dates(start_date, end_date)
        with _client() as client:
            transactions = client.list_transactions(plan_id, resolved_start, resolved_end, limit)
        return {"transactions": transactions}

    return _tool_call(run)


@mcp.tool
def list_payees(plan_id: str = "default") -> dict[str, Any]:
    """List payees for a YNAB plan."""

    def run() -> dict[str, Any]:
        with _client() as client:
            return {"payees": client.list_payees(plan_id)}

    return _tool_call(run)


if __name__ == "__main__":
    mcp.run()
