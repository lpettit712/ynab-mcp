from datetime import date

from ynab_mcp.summaries import (
    current_month,
    daily_checkin_summary,
    format_milliunits,
    largest_transactions_summary,
    spending_by_category_summary,
    spending_by_payee_summary,
)


def test_current_month_formats_year_and_month():
    assert current_month(date(2026, 4, 25)) == "2026-04"


def test_format_milliunits_converts_to_currency_string():
    assert format_milliunits(123456) == "123.46"
    assert format_milliunits(-123456) == "-123.46"


def test_daily_checkin_summary_filters_accounts_categories_and_transactions():
    accounts = [
        {
            "id": "a1",
            "name": "Checking",
            "type": "checking",
            "closed": False,
            "on_budget": True,
            "balance": 250000,
            "balance_formatted": "$250.00",
        },
        {
            "id": "a2",
            "name": "Closed Card",
            "type": "creditCard",
            "closed": True,
            "on_budget": True,
            "balance": -1000,
        },
    ]
    categories = [
        {
            "id": "c1",
            "name": "Groceries",
            "category_group_name": "Everyday",
            "hidden": False,
            "deleted": False,
            "balance": -12000,
            "balance_formatted": "-$12.00",
        },
        {
            "id": "c2",
            "name": "Dining",
            "category_group_name": "Everyday",
            "hidden": False,
            "deleted": False,
            "balance": 3500,
            "balance_formatted": "$3.50",
        },
        {
            "id": "c3",
            "name": "Hidden",
            "category_group_name": "Old",
            "hidden": True,
            "deleted": False,
            "balance": 5000,
        },
    ]
    transactions = [
        {
            "id": "t1",
            "date": "2026-04-25",
            "payee_name": "Market",
            "category_name": "Groceries",
            "amount": -4800,
            "amount_formatted": "-$4.80",
        },
        {
            "id": "t2",
            "date": "2026-04-24",
            "payee_name": "Employer",
            "category_name": "Inflow: Ready to Assign",
            "amount": 100000,
        },
    ]

    summary = daily_checkin_summary(accounts, categories, transactions)

    assert summary["accounts"] == [
        {
            "name": "Checking",
            "type": "checking",
            "balance": "$250.00",
            "on_budget": True,
        }
    ]
    assert summary["overspent_categories"] == [
        {
            "name": "Groceries",
            "group": "Everyday",
            "balance": "-$12.00",
        }
    ]
    assert summary["low_categories"] == [
        {
            "name": "Dining",
            "group": "Everyday",
            "balance": "$3.50",
        }
    ]
    assert summary["recent_transactions"][0]["payee"] == "Market"


def test_spending_by_category_summary_groups_outflows_only():
    transactions = [
        {"category_name": "Groceries", "amount": -2500, "amount_currency": -25.0},
        {"category_name": "Groceries", "amount": -500, "amount_currency": -5.0},
        {"category_name": "Income", "amount": 100000, "amount_currency": 1000.0},
        {"category_name": None, "amount": -750},
    ]

    summary = spending_by_category_summary(transactions)

    assert summary["groups"] == [
        {"category": "Groceries", "amount": "30.00", "transaction_count": 2},
        {"category": "Uncategorized", "amount": "0.75", "transaction_count": 1},
    ]
    assert summary["total_spent"] == "30.75"


def test_spending_by_payee_summary_groups_outflows_only():
    transactions = [
        {"payee_name": "Market", "amount": -2500},
        {"payee_name": "Market", "amount": -500},
        {"payee_name": "Employer", "amount": 100000},
    ]

    summary = spending_by_payee_summary(transactions)

    assert summary["groups"] == [
        {"payee": "Market", "amount": "3.00", "transaction_count": 2}
    ]
    assert summary["total_spent"] == "3.00"


def test_largest_transactions_summary_sorts_largest_outflows():
    transactions = [
        {
            "date": "2026-04-20",
            "payee_name": "Coffee",
            "category_name": "Dining",
            "amount": -650,
        },
        {
            "date": "2026-04-21",
            "payee_name": "Rent",
            "category_name": "Rent",
            "amount": -150000,
        },
        {
            "date": "2026-04-22",
            "payee_name": "Employer",
            "category_name": "Income",
            "amount": 500000,
        },
    ]

    summary = largest_transactions_summary(transactions, limit=1)

    assert summary["transactions"] == [
        {
            "date": "2026-04-21",
            "payee": "Rent",
            "category": "Rent",
            "amount": "150.00",
        }
    ]
