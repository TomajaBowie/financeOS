import pytest
from decimal import Decimal


class TestBudgetExceeded:
    def test_budget_not_exceeded_at_exact_limit(self, client, auth_headers, test_account):
        """
        Bug: is_budget_exceeded uses >= so alert fires at exact limit.
        Fix: use > so alert only fires when strictly exceeded.
        """
        account_id = test_account["id"]

        budget = client.post("/api/budgets", json={
            "category_id": 1,
            "amount_limit": "100.00",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30"
        }, headers=auth_headers).json()

        client.post("/api/transactions", json={
            "account_id": account_id,
            "category_id": 1,
            "amount": "100.00",
            "transaction_type": "expense",
            "description": "Exact limit spend",
            "transaction_date": "2026-06-10T10:00:00"
        }, headers=auth_headers)

        status = client.get(
            f"/api/budgets/{budget['id']}/status",
            headers=auth_headers
        ).json()

        assert status["is_exceeded"] == False, \
            f"Budget at exact limit should not be exceeded but is_exceeded={status['is_exceeded']}"
        assert float(status["spent"]) == 100.0
        assert float(status["remaining"]) == 0.0

    def test_budget_exceeded_one_cent_over(self, client, auth_headers, test_account):
        account_id = test_account["id"]

        budget = client.post("/api/budgets", json={
            "category_id": 2,
            "amount_limit": "100.00",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30"
        }, headers=auth_headers).json()

        client.post("/api/transactions", json={
            "account_id": account_id,
            "category_id": 2,
            "amount": "100.01",
            "transaction_type": "expense",
            "description": "One cent over",
            "transaction_date": "2026-06-10T10:00:00"
        }, headers=auth_headers)

        status = client.get(
            f"/api/budgets/{budget['id']}/status",
            headers=auth_headers
        ).json()

        assert status["is_exceeded"] == True


class TestActiveBudgets:
    def test_expired_budget_not_in_active_list(self, client, auth_headers):
        """
        Bug: get_active_budgets returns all is_active=True
        including expired periods.
        Fix: filter by period_end >= today.
        """
        expired_budget = client.post("/api/budgets", json={
            "category_id": 3,
            "amount_limit": "50.00",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31"
        }, headers=auth_headers).json()

        active_budget = client.post("/api/budgets", json={
            "category_id": 4,
            "amount_limit": "75.00",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30"
        }, headers=auth_headers).json()

        response = client.get("/api/budgets", headers=auth_headers)
        budgets = response.json()

        budget_ids = [b["id"] for b in budgets]
        assert expired_budget["id"] not in budget_ids, \
            "Expired budget should not appear in active budgets list"
        assert active_budget["id"] in budget_ids