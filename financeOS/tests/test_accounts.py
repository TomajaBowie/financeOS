import pytest


class TestAccountTransfer:
    def test_transfer_debits_source_correctly(self, client, auth_headers):
        """
        Bug: transfer credits destination before debiting source.
        If something fails mid-transfer, destination keeps money.
        Fix: debit source first, then credit destination atomically.
        """
        acc1 = client.post("/api/accounts", json={
            "name": "Source Account",
            "account_type": "checking",
            "initial_balance": "1000.00",
            "currency": "USD"
        }, headers=auth_headers).json()

        acc2 = client.post("/api/accounts", json={
            "name": "Destination Account",
            "account_type": "savings",
            "initial_balance": "500.00",
            "currency": "USD"
        }, headers=auth_headers).json()

        client.post(
            "/api/accounts/transfer",
            params={
                "source_id": acc1["id"],
                "destination_id": acc2["id"],
                "amount": "200.00"
            },
            headers=auth_headers
        )

        updated_source = client.get(
            f"/api/accounts/{acc1['id']}",
            headers=auth_headers
        ).json()
        updated_dest = client.get(
            f"/api/accounts/{acc2['id']}",
            headers=auth_headers
        ).json()

        assert float(updated_source["balance"]) == 800.0, \
            f"Source should be 800 but got {updated_source['balance']}"
        assert float(updated_dest["balance"]) == 700.0, \
            f"Destination should be 700 but got {updated_dest['balance']}"
        assert float(updated_source["balance"]) + float(updated_dest["balance"]) == 1500.0, \
            "Total balance should be conserved across transfer"