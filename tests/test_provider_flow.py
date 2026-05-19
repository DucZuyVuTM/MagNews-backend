"""
Тестовый сценарий 9: Регистрация поставщика и одобрение администратором.
Тестовый сценарий 10: Создание новой подписки поставщиком.
Чек-лист 10, 11 — регистрация поставщика и публикация изданий.
"""
from fastapi.testclient import TestClient


class TestProviderRegistration:
    """
    Чек-лист 10 — регистрация поставщика и публикация изданий.
    """

    def test_register_provider_creates_account_with_provider_role(
        self, client: TestClient
    ):
        response = client.post(
            "/api/users/register-provider",
            json={
                "email": "new.provider@example.com",
                "username": "new_provider",
                "full_name": "New Provider Co",
                "password": "ProviderPass123",
                "company_name": "New Provider LLC",
                "inn": "7712345678",
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["role"] == "provider"
        assert body["company_name"] == "New Provider LLC"
        assert body["inn"] == "7712345678"

    def test_register_provider_rejects_duplicate_email(self, client: TestClient):
        payload = {
            "email": "dup@example.com",
            "username": "dup_username",
            "full_name": "Dup Provider",
            "password": "ProviderPass123",
            "company_name": "Dup LLC",
            "inn": None,
        }
        first = client.post("/api/users/register-provider", json=payload)
        assert first.status_code == 201

        payload["username"] = "another_username"
        second = client.post("/api/users/register-provider", json=payload)
        assert second.status_code == 400


class TestProviderPublicationFlow:
    """
    Поставщик создаёт публикацию → статус pending → админ одобряет → каталог
    отображает.
    """

    def _provider_creates_publication(
        self, client: TestClient, provider_auth_headers: dict
    ) -> int:
        response = client.post(
            "/api/publications/",
            headers=provider_auth_headers,
            json={
                "title": "Provider's Magazine",
                "description": "Awaiting moderation",
                "type": "magazine",
                "publisher": "Provider LLC",
                "frequency": "monthly",
                "price_monthly": 12.0,
                "price_yearly": 120.0,
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["moderation_status"] == "pending"
        return body["id"]

    def test_provider_publication_is_hidden_from_catalog_until_approved(
        self, client: TestClient, provider_auth_headers
    ):
        self._provider_creates_publication(client, provider_auth_headers)

        listing = client.get("/api/publications/").json()
        titles = [p["title"] for p in listing]
        assert "Provider's Magazine" not in titles

    def test_admin_approves_publication_then_it_appears_in_catalog(
        self,
        client: TestClient,
        provider_auth_headers,
        admin_auth_headers,
    ):
        pub_id = self._provider_creates_publication(client, provider_auth_headers)

        moderate = client.post(
            f"/api/publications/{pub_id}/moderate",
            headers=admin_auth_headers,
            json={"decision": "approve"},
        )
        assert moderate.status_code == 200
        assert moderate.json()["moderation_status"] == "approved"

        listing = client.get("/api/publications/").json()
        titles = [p["title"] for p in listing]
        assert "Provider's Magazine" in titles

    def test_admin_rejects_publication_with_note(
        self,
        client: TestClient,
        provider_auth_headers,
        admin_auth_headers,
    ):
        pub_id = self._provider_creates_publication(client, provider_auth_headers)

        moderate = client.post(
            f"/api/publications/{pub_id}/moderate",
            headers=admin_auth_headers,
            json={"decision": "reject", "note": "Картинка-обложка отсутствует"},
        )
        assert moderate.status_code == 200
        body = moderate.json()
        assert body["moderation_status"] == "rejected"
        assert body["moderation_note"] == "Картинка-обложка отсутствует"

    def test_regular_user_cannot_create_publication(
        self, client: TestClient, user_auth_headers
    ):
        response = client.post(
            "/api/publications/",
            headers=user_auth_headers,
            json={
                "title": "Hack attempt",
                "type": "magazine",
                "price_monthly": 1.0,
                "price_yearly": 10.0,
            },
        )
        assert response.status_code == 403

    def test_provider_cannot_moderate_own_publication(
        self,
        client: TestClient,
        provider_auth_headers,
    ):
        pub_id = self._provider_creates_publication(client, provider_auth_headers)
        response = client.post(
            f"/api/publications/{pub_id}/moderate",
            headers=provider_auth_headers,
            json={"decision": "approve"},
        )
        assert response.status_code == 403

    def test_provider_sees_own_pending_in_mine_listing(
        self, client: TestClient, provider_auth_headers
    ):
        pub_id = self._provider_creates_publication(client, provider_auth_headers)
        response = client.get("/api/publications/mine", headers=provider_auth_headers)
        assert response.status_code == 200
        ids = [p["id"] for p in response.json()]
        assert pub_id in ids

    def test_admin_sees_pending_in_pending_listing(
        self,
        client: TestClient,
        provider_auth_headers,
        admin_auth_headers,
    ):
        pub_id = self._provider_creates_publication(client, provider_auth_headers)
        response = client.get("/api/publications/pending", headers=admin_auth_headers)
        assert response.status_code == 200
        ids = [p["id"] for p in response.json()]
        assert pub_id in ids
