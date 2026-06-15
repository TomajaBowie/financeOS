import pytest
from datetime import datetime


class TestTransactionDateFilter:
    def test_end_date_inclusive(self, client, auth_headers, test_account):
        """
        Bug: end_date filter uses < instead of <=
        so transactions on the end date are excluded.
        Fix: change to <= on end_date filter.
        """
        account_id = test_account["id"]

        client.post("/api/transactions", json={
            "account_id": account_id,
            "amount": "100.00",
            "transaction_type": "expense",
            "description": "End date transaction",
            "transaction_date": "2026-06-30T23:59:00"
        }, headers=auth_headers)

        response = client.get(
            "/api/transactions",
            params={
                "start_date": "2026-06-01T00:00:00",
                "end_date": "2026-06-30T23:59:00"
            },
            headers=auth_headers
        )
        data = response.json()
        assert data["total"] == 1, \
            f"Transaction on end date should be included but total is {data['total']}"

    def test_start_date_inclusive(self, client, auth_headers, test_account):
        account_id = test_account["id"]

        client.post("/api/transactions", json={
            "account_id": account_id,
            "amount": "50.00",
            "transaction_type": "income",
            "description": "Start date transaction",
            "transaction_date": "2026-06-01T00:00:00"
        }, headers=auth_headers)

        response = client.get(
            "/api/transactions",
            params={
                "start_date": "2026-06-01T00:00:00",
                "end_date": "2026-06-30T23:59:00"
            },
            headers=auth_headers
        )
        data = response.json()
        assert data["total"] >= 1


class TestTransactionDeleteBalance:
    def test_delete_expense_restores_balance(self, client, auth_headers, test_account):
        """
        Bug: deleting a transaction does not reverse
        the balance effect on the account.
        Fix: reverse income/expense on delete.
        """
        account_id = test_account["id"]
        initial_balance = float(test_account["balance"])

        tx_response = client.post("/api/transactions", json={
            "account_id": account_id,
            "amount": "200.00",
            "transaction_type": "expense",
            "description": "Test expense",
            "transaction_date": "2026-06-10T10:00:00"
        }, headers=auth_headers)
        tx_id = tx_response.json()["id"]

        after_expense = client.get(
            f"/api/accounts/{account_id}",
            headers=auth_headers
        ).json()
        assert float(after_expense["balance"]) == initial_balance - 200

        client.delete(f"/api/transactions/{tx_id}", headers=auth_headers)

        after_delete = client.get(
            f"/api/accounts/{account_id}",
            headers=auth_headers
        ).json()
        assert float(after_delete["balance"]) == initial_balance, \
            f"Balance should be restored to {initial_balance} after delete but got {after_delete['balance']}"

    def test_delete_income_restores_balance(self, client, auth_headers, test_account):
        account_id = test_account["id"]
        initial_balance = float(test_account["balance"])

        tx_response = client.post("/api/transactions", json={
            "account_id": account_id,
            "amount": "500.00",
            "transaction_type": "income",
            "description": "Test income",
            "transaction_date": "2026-06-10T10:00:00"
        }, headers=auth_headers)
        tx_id = tx_response.json()["id"]

        client.delete(f"/api/transactions/{tx_id}", headers=auth_headers)

        after_delete = client.get(
            f"/api/accounts/{account_id}",
            headers=auth_headers
        ).json()
        assert float(after_delete["balance"]) == initial_balance, \
            f"Balance should be restored after income deletion"


class TestMonthlySummary:
    def test_last_day_of_month_included(self, client, auth_headers, test_account):
        """
        Bug: monthly summary uses < on month_end
        so transactions on the last day are excluded.
        Fix: use <= on month_end boundary.
        """
        account_id = test_account["id"]

        client.post("/api/transactions", json={
            "account_id": account_id,
            "amount": "300.00",
            "transaction_type": "expense",
            "description": "Last day of month expense",
            "transaction_date": "2026-06-30T15:00:00"
        }, headers=auth_headers)

        response = client.get(
            "/api/transactions/summary/monthly",
            params={"year": 2026, "month": 6},
            headers=auth_headers
        )
        data = response.json()
        assert float(data["expenses"]) == 300.0, \
            f"Last day transaction should be in summary but expenses={data['expenses']}"