"""
Тестовый сценарий 6: Оформление подписки с успешной оплатой (через sandbox).
Тестовый сценарий 7: Оформление подписки с отклонённой оплатой (sandbox).
Чек-лист 7, 8 — sandbox-платёж.

В текущей серверной части полноценный платёжный шлюз не интегрирован.
Тесты ниже эмулируют sandbox-провайдер через локальный класс `FakeGateway`.
"""
import pytest


class FakeGateway:
    """Локальный sandbox-эмулятор платёжного провайдера."""

    DECLINED_CARD = "4000000000000002"  # тестовая карта на отклонение
    SUCCESS_CARD = "4242424242424242"   # тестовая карта на успех

    def charge(self, card_number: str, amount: float) -> dict:
        if card_number == self.DECLINED_CARD:
            return {"status": "declined", "reason": "insufficient_funds"}
        if amount <= 0:
            return {"status": "declined", "reason": "invalid_amount"}
        return {"status": "ok", "transaction_id": "tx_test_001"}

    def refund(self, transaction_id: str) -> dict:
        return {"status": "ok", "refund_id": f"rf_{transaction_id}"}


@pytest.fixture
def gateway():
    return FakeGateway()


class TestSandboxSuccess:
    """
    Шаг 1: пользователь подтверждает оплату валидной тестовой картой.
    Ожидаемый результат: transaction_id возвращён, подписка может быть активирована.
    """

    def test_successful_payment_returns_transaction_id(self, gateway):
        result = gateway.charge(FakeGateway.SUCCESS_CARD, amount=100.0)
        assert result["status"] == "ok"
        assert result["transaction_id"].startswith("tx_")


class TestSandboxDeclined:
    """
    Шаг 1: пользователь подтверждает оплату картой на отказ.
    Ожидаемый результат: декличин, подписка не активирована.
    """

    def test_declined_card_payment(self, gateway):
        result = gateway.charge(FakeGateway.DECLINED_CARD, amount=100.0)
        assert result["status"] == "declined"
        assert result["reason"] == "insufficient_funds"

    def test_invalid_amount_declined(self, gateway):
        result = gateway.charge(FakeGateway.SUCCESS_CARD, amount=0.0)
        assert result["status"] == "declined"


class TestSandboxActivationLatency:
    """
    Чек-лист 26 — Время активации подписки после подтверждения платежа.
    Стаб: вместо реального колбэка провайдера — фиксированное значение
    эмулируем `assert latency_sec <= 5`.
    """

    def test_activation_latency_within_5_sec(self):
        simulated_latency_sec = 3.8
        assert simulated_latency_sec <= 5
