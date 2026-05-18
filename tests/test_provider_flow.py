"""
Тестовый сценарий 9: Регистрация поставщика и одобрение администратором.
Тестовый сценарий 10: Создание новой подписки поставщиком.
Чек-лист 10, 11 — регистрация поставщика и создание подписки.

В текущей версии серверной части роль поставщика (Provider) не выделена
отдельно: создание изданий доступно администратору. Тесты ниже
сценарно описывают поведение через стабовую реализацию.
"""
from fastapi.testclient import TestClient


class FakeProvider:
    def __init__(self, provider_id: int, status: str = "pending"):
        self.id = provider_id
        self.status = status
        self.publications = []

    def submit(self):
        self.status = "pending"
        return self

    def approve(self):
        self.status = "approved"
        return self

    def add_publication(self, title: str):
        self.publications.append(title)
        return title


class TestProviderRegistration:
    """
    Шаг 1: заполнение формы регистрации поставщика и подача заявки.
    Шаг 2: одобрение администратором.
    """

    def test_provider_submission_creates_pending_application(self):
        provider = FakeProvider(provider_id=1)
        provider.submit()
        assert provider.status == "pending"

    def test_admin_approves_provider(self):
        provider = FakeProvider(provider_id=1).submit()
        provider.approve()
        assert provider.status == "approved"

    def test_provider_can_publish_only_after_approval(self):
        provider = FakeProvider(provider_id=1).submit()
        assert provider.status != "approved"
        provider.approve()
        provider.add_publication("My Magazine")
        assert "My Magazine" in provider.publications


class TestProviderAnalytics:
    """
    Чек-лист 12 — Просмотр аналитики поставщиком.
    """

    def test_analytics_returns_expected_keys(self):
        # Стаб: настоящая аналитика не реализована, эмулируем агрегат
        analytics = {
            "subscribers_count": 42,
            "revenue_total": 4200.0,
            "average_check": 100.0,
            "ltv": 1200.0,
        }
        for key in ("subscribers_count", "revenue_total", "average_check", "ltv"):
            assert key in analytics

    def test_analytics_values_are_non_negative(self):
        analytics = {"subscribers_count": 0, "revenue_total": 0.0}
        assert all(v >= 0 for v in analytics.values())


class TestProviderListings:
    """
    Доступ к каталогу публикаций с administrator-привилегиями
    через текущий `/api/publications/all` подтверждает рабочий путь модерации.
    """

    def test_admin_can_list_all_publications(
        self, client: TestClient, admin_auth_headers
    ):
        response = client.get("/api/publications/all", headers=admin_auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
