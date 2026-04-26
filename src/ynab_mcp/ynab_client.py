from __future__ import annotations

from typing import Any

import httpx

from ynab_mcp.config import get_settings


BASE_URL = "https://api.ynab.com/v1"


class YnabApiError(RuntimeError):
    def __init__(self, status_code: int, error_type: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type
        self.message = message


class YnabClient:
    def __init__(self, access_token: str, http_client: httpx.Client | None = None):
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=30)
        self._headers = {"Authorization": f"Bearer {access_token}"}

    @classmethod
    def from_env(cls) -> "YnabClient":
        settings = get_settings()
        return cls(settings.access_token)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "YnabClient":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def list_plans(self) -> list[dict[str, Any]]:
        return self._get("/plans").get("plans", [])

    def get_plan_summary(self, plan_id: str = "default") -> dict[str, Any]:
        return self._get(f"/plans/{plan_id}").get("plan", {})

    def list_accounts(self, plan_id: str = "default") -> list[dict[str, Any]]:
        return self._get(f"/plans/{plan_id}/accounts").get("accounts", [])

    def list_categories(self, plan_id: str = "default", month: str = "current") -> list[dict[str, Any]]:
        return self._get(f"/plans/{plan_id}/months/{month}/categories").get("categories", [])

    def list_transactions(
        self,
        plan_id: str = "default",
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params = {"since_date": start_date} if start_date else None
        transactions = self._get(f"/plans/{plan_id}/transactions", params=params).get("transactions", [])
        if end_date:
            transactions = [item for item in transactions if str(item.get("date", "")) <= end_date]
        return transactions[: max(0, limit)]

    def list_payees(self, plan_id: str = "default") -> list[dict[str, Any]]:
        return self._get(f"/plans/{plan_id}/payees").get("payees", [])

    def _get(self, path: str, params: dict[str, str | None] | None = None) -> dict[str, Any]:
        try:
            response = self._client.get(
                f"{BASE_URL}{path}",
                headers=self._headers,
                params={key: value for key, value in (params or {}).items() if value},
            )
        except httpx.RequestError as exc:
            raise YnabApiError(0, "network", f"Could not reach YNAB API: {exc}") from exc
        if response.status_code >= 400:
            raise self._api_error(response)
        payload = response.json()
        return payload.get("data", {})

    def _api_error(self, response: httpx.Response) -> YnabApiError:
        detail = ""
        name = ""
        try:
            error = response.json().get("error", {})
            detail = str(error.get("detail") or "")
            name = str(error.get("name") or "")
        except ValueError:
            detail = response.text
        error_type = {
            401: "authentication",
            403: "permission",
            404: "not_found",
            429: "rate_limit",
        }.get(response.status_code, "ynab_api")
        message = detail or name or f"YNAB API returned HTTP {response.status_code}"
        return YnabApiError(response.status_code, error_type, message)
