import httpx
import pytest

from ynab_mcp.ynab_client import YnabApiError, YnabClient


def json_response(status_code, payload, request):
    return httpx.Response(status_code, json=payload, request=request)


def test_list_plans_uses_bearer_token_and_unwraps_data():
    requests = []

    def handler(request):
        requests.append(request)
        return json_response(
            200,
            {"data": {"plans": [{"id": "p1", "name": "Main Plan"}]}},
            request,
        )

    client = YnabClient("secret-token", http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    assert client.list_plans() == [{"id": "p1", "name": "Main Plan"}]
    assert requests[0].headers["authorization"] == "Bearer secret-token"
    assert str(requests[0].url) == "https://api.ynab.com/v1/plans"


def test_get_plan_summary_uses_plan_endpoint():
    def handler(request):
        assert request.url.path == "/v1/plans/default"
        return json_response(200, {"data": {"plan": {"id": "default", "name": "Plan"}}}, request)

    client = YnabClient("secret-token", http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    assert client.get_plan_summary("default") == {"id": "default", "name": "Plan"}


@pytest.mark.parametrize(
    ("method_name", "path"),
    [
        ("list_accounts", "/v1/plans/default/accounts"),
        ("list_payees", "/v1/plans/default/payees"),
    ],
)
def test_collection_methods_use_expected_paths(method_name, path):
    def handler(request):
        assert request.url.path == path
        key = "accounts" if method_name == "list_accounts" else "payees"
        return json_response(200, {"data": {key: []}}, request)

    client = YnabClient("secret-token", http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    assert getattr(client, method_name)("default") == []


def test_list_categories_uses_current_month_categories_endpoint():
    def handler(request):
        assert request.url.path == "/v1/plans/default/months/2026-04/categories"
        return json_response(200, {"data": {"categories": [{"id": "c1"}]}}, request)

    client = YnabClient("secret-token", http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    assert client.list_categories("default", "2026-04") == [{"id": "c1"}]


def test_list_transactions_sends_since_date_and_filters_end_date_and_limit():
    def handler(request):
        assert request.url.path == "/v1/plans/default/transactions"
        assert request.url.params["since_date"] == "2026-04-01"
        return json_response(
            200,
            {
                "data": {
                    "transactions": [
                        {"id": "t1", "date": "2026-04-20"},
                        {"id": "t2", "date": "2026-05-01"},
                        {"id": "t3", "date": "2026-04-21"},
                    ]
                }
            },
            request,
        )

    client = YnabClient("secret-token", http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    assert client.list_transactions("default", start_date="2026-04-01", end_date="2026-04-30", limit=1) == [
        {"id": "t1", "date": "2026-04-20"}
    ]


def test_error_mapping_does_not_include_token():
    def handler(request):
        return json_response(
            401,
            {"error": {"id": "401", "name": "unauthorized", "detail": "bad token"}},
            request,
        )

    client = YnabClient("secret-token", http_client=httpx.Client(transport=httpx.MockTransport(handler)))

    with pytest.raises(YnabApiError) as exc:
        client.list_plans()

    assert exc.value.status_code == 401
    assert exc.value.error_type == "authentication"
    assert "secret-token" not in str(exc.value)
