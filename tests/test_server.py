from ynab_mcp.config import SettingsError
from ynab_mcp.ynab_client import YnabApiError
import ynab_mcp.server as server


class FakeClient:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def list_plans(self):
        return [{"id": "p1", "name": "Main Plan"}]

    def get_plan_summary(self, plan_id="default"):
        return {"id": plan_id, "name": "Main Plan"}

    def list_accounts(self, plan_id="default"):
        return [{"id": "a1", "name": "Checking", "balance": 1000}]

    def list_categories(self, plan_id="default", month="current"):
        return [{"id": "c1", "name": "Groceries", "balance": 5000}]

    def list_transactions(self, plan_id="default", start_date=None, end_date=None, limit=100):
        return [{"id": "t1", "date": "2026-04-25", "amount": -1200}]

    def list_payees(self, plan_id="default"):
        return [{"id": "payee-1", "name": "Market"}]


def test_raw_tool_functions_return_expected_shapes(monkeypatch):
    monkeypatch.setattr(server, "_client", lambda: FakeClient())

    assert server.list_plans() == {"plans": [{"id": "p1", "name": "Main Plan"}]}
    assert server.get_plan_summary() == {"plan": {"id": "default", "name": "Main Plan"}}
    assert server.list_accounts() == {"accounts": [{"id": "a1", "name": "Checking", "balance": 1000}]}
    assert server.list_categories(month="2026-04") == {
        "categories": [{"id": "c1", "name": "Groceries", "balance": 5000}]
    }
    assert server.list_transactions(limit=1) == {
        "transactions": [{"id": "t1", "date": "2026-04-25", "amount": -1200}]
    }
    assert server.list_payees() == {"payees": [{"id": "payee-1", "name": "Market"}]}


def test_tool_error_for_missing_token(monkeypatch):
    def fail():
        raise SettingsError("Missing YNAB_ACCESS_TOKEN. Set it in your environment before starting ynab-mcp.")

    monkeypatch.setattr(server, "_client", fail)

    assert server.list_plans() == {
        "error": {
            "type": "configuration",
            "message": "Missing YNAB_ACCESS_TOKEN. Set it in your environment before starting ynab-mcp.",
        }
    }


def test_tool_error_for_rate_limit(monkeypatch):
    class FailingClient(FakeClient):
        def list_plans(self):
            raise YnabApiError(429, "rate_limit", "Too many requests")

    monkeypatch.setattr(server, "_client", lambda: FailingClient())

    assert server.list_plans() == {
        "error": {
            "type": "rate_limit",
            "status_code": 429,
            "message": "Too many requests",
        }
    }
