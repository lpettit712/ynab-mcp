from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable


LOW_CATEGORY_THRESHOLD_MILLIUNITS = 5000


def current_month(today: date | None = None) -> str:
    value = today or date.today()
    return value.strftime("%Y-%m")


def format_milliunits(amount: int | float | None) -> str:
    value = Decimal(str(amount or 0)) / Decimal("1000")
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def display_amount(item: dict[str, Any], prefix: str = "amount") -> str:
    formatted = item.get(f"{prefix}_formatted")
    if formatted:
        return str(formatted)
    currency = item.get(f"{prefix}_currency")
    if currency is not None:
        return f"{Decimal(str(currency)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"
    return format_milliunits(item.get(prefix, 0))


def _amount_milliunits(item: dict[str, Any]) -> int:
    return int(item.get("amount") or 0)


def _category_balance(item: dict[str, Any]) -> int:
    return int(item.get("balance") or 0)


def _format_decimal_amount(amount: Decimal) -> str:
    return str(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _outflow_amount_value(item: dict[str, Any]) -> Decimal:
    amount = _amount_milliunits(item)
    if amount >= 0:
        return Decimal("0")
    currency = item.get("amount_currency")
    if currency is not None:
        return abs(Decimal(str(currency)))
    return abs(Decimal(amount) / Decimal("1000"))


def daily_checkin_summary(
    accounts: Iterable[dict[str, Any]],
    categories: Iterable[dict[str, Any]],
    transactions: Iterable[dict[str, Any]],
    recent_limit: int = 5,
) -> dict[str, Any]:
    active_accounts = [
        {
            "name": account.get("name"),
            "type": account.get("type"),
            "balance": display_amount(account, "balance"),
            "on_budget": bool(account.get("on_budget")),
        }
        for account in accounts
        if not account.get("closed")
    ]

    visible_categories = [
        category
        for category in categories
        if not category.get("hidden") and not category.get("deleted")
    ]
    overspent = [
        {
            "name": category.get("name"),
            "group": category.get("category_group_name"),
            "balance": display_amount(category, "balance"),
        }
        for category in visible_categories
        if _category_balance(category) < 0
    ]
    low = [
        {
            "name": category.get("name"),
            "group": category.get("category_group_name"),
            "balance": display_amount(category, "balance"),
        }
        for category in visible_categories
        if 0 <= _category_balance(category) <= LOW_CATEGORY_THRESHOLD_MILLIUNITS
    ]
    recent = [
        {
            "date": transaction.get("date"),
            "payee": transaction.get("payee_name") or "Unknown",
            "category": transaction.get("category_name") or "Uncategorized",
            "amount": display_amount(transaction),
        }
        for transaction in list(transactions)[:recent_limit]
    ]
    return {
        "accounts": active_accounts,
        "overspent_categories": overspent,
        "low_categories": low,
        "recent_transactions": recent,
    }


def spending_by_category_summary(transactions: Iterable[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    counts: dict[str, int] = defaultdict(int)
    for transaction in transactions:
        amount = _outflow_amount_value(transaction)
        if amount == 0:
            continue
        key = transaction.get("category_name") or "Uncategorized"
        totals[key] += amount
        counts[key] += 1
    groups = [
        {
            "category": key,
            "amount": _format_decimal_amount(total),
            "transaction_count": counts[key],
        }
        for key, total in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]
    return {"groups": groups, "total_spent": _format_decimal_amount(sum(totals.values()))}


def spending_by_payee_summary(transactions: Iterable[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    counts: dict[str, int] = defaultdict(int)
    for transaction in transactions:
        amount = _outflow_amount_value(transaction)
        if amount == 0:
            continue
        key = transaction.get("payee_name") or "Unknown"
        totals[key] += amount
        counts[key] += 1
    groups = [
        {
            "payee": key,
            "amount": _format_decimal_amount(total),
            "transaction_count": counts[key],
        }
        for key, total in sorted(totals.items(), key=lambda item: item[1], reverse=True)
    ]
    return {"groups": groups, "total_spent": _format_decimal_amount(sum(totals.values()))}


def largest_transactions_summary(
    transactions: Iterable[dict[str, Any]], limit: int = 10
) -> dict[str, Any]:
    outflows = [item for item in transactions if _amount_milliunits(item) < 0]
    largest = sorted(outflows, key=lambda item: abs(_amount_milliunits(item)), reverse=True)[
        :limit
    ]
    return {
        "transactions": [
            {
                "date": item.get("date"),
                "payee": item.get("payee_name") or "Unknown",
                "category": item.get("category_name") or "Uncategorized",
                "amount": format_milliunits(abs(_amount_milliunits(item))),
            }
            for item in largest
        ]
    }
