"""
Чек-лист 15, 16, 17, 26 — производительность и UX.

Полноценный замер метрик (Lighthouse / Locust / BrowserStack) не выполняется
in-process. Тесты ниже выполняют smoke-замеры времени ответа основных
эндпоинтов и фиксируют, что значения вписываются в SLA из НФР проекта.
"""
import time

from fastapi.testclient import TestClient


class TestEndpointLatency:
    """
    SLA из НФР: время реакции (кроме оплаты) ≤ 2 сек.
    """

    def test_root_under_2sec(self, client: TestClient):
        start = time.perf_counter()
        response = client.get("/")
        elapsed = time.perf_counter() - start
        assert response.status_code == 200
        assert elapsed < 2.0

    def test_catalog_list_under_1sec(
        self, client: TestClient, sample_publication
    ):
        start = time.perf_counter()
        response = client.get("/api/publications/")
        elapsed = time.perf_counter() - start
        assert response.status_code == 200
        assert elapsed < 1.0


class TestResponsiveDesignMarker:
    """
    Чек-лист 16 — адаптивность интерфейса.
    Проверяется на стороне фронта в Playwright; здесь стаб-маркер,
    что серверная часть не делает предположений о User-Agent.
    """

    def test_no_user_agent_dependency(self, client: TestClient):
        ua1 = client.get("/", headers={"User-Agent": "Mobile/iPhone"})
        ua2 = client.get("/", headers={"User-Agent": "Mozilla/5.0 Desktop"})
        assert ua1.status_code == 200 and ua2.status_code == 200
        assert ua1.json() == ua2.json()
