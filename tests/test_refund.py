"""
Чек-лист 21 — Возврат средств по решению администратора.

Серверная часть в текущей версии не интегрирована с реальным платёжным
провайдером; возврат эмулируется через стабовый sandbox-вызов.
"""


class FakeRefundGateway:
    def initiate_refund(self, transaction_id: str, amount: float) -> dict:
        if amount <= 0:
            return {"status": "error", "code": "invalid_amount"}
        return {
            "status": "ok",
            "refund_id": f"rf_{transaction_id}",
            "amount": amount,
        }


class TestRefund:
    def test_refund_returns_ok_for_valid_transaction(self):
        gateway = FakeRefundGateway()
        result = gateway.initiate_refund("tx_test_001", amount=100.0)
        assert result["status"] == "ok"
        assert result["refund_id"].startswith("rf_")
        assert result["amount"] == 100.0

    def test_refund_rejects_zero_amount(self):
        gateway = FakeRefundGateway()
        result = gateway.initiate_refund("tx_test_001", amount=0.0)
        assert result["status"] == "error"
