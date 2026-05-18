"""
Тестовый сценарий 6: Оформление подписки с успешной оплатой (позитивный).
Тестовый сценарий 7: Оформление подписки с отклонённой оплатой (негативный).
Тестовый сценарий 8: Отмена подписки (позитивный).
"""
from fastapi.testclient import TestClient


class TestSubscriptionCreate:
    """
    Чек-лист 7 — оформление подписки (позитивный).
    """

    def test_create_subscription_success(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        response = client.post(
            "/api/subscriptions/",
            json={
                "publication_id": sample_publication.id,
                "duration_months": 1,
                "auto_renew": False,
            },
            headers=user_auth_headers,
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["publication_id"] == sample_publication.id
        assert data["status"] == "active"
        assert data["price"] == 10.0
        assert data["publication"]["title"] == sample_publication.title

    def test_create_subscription_yearly_pricing(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        response = client.post(
            "/api/subscriptions/",
            json={
                "publication_id": sample_publication.id,
                "duration_months": 12,
                "auto_renew": True,
            },
            headers=user_auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["price"] == 100.0

    def test_create_subscription_requires_auth(
        self, client: TestClient, sample_publication
    ):
        response = client.post(
            "/api/subscriptions/",
            json={
                "publication_id": sample_publication.id,
                "duration_months": 1,
                "auto_renew": False,
            },
        )
        assert response.status_code == 401

    def test_duplicate_active_subscription_rejected(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        client.post(
            "/api/subscriptions/",
            json={
                "publication_id": sample_publication.id,
                "duration_months": 1,
                "auto_renew": False,
            },
            headers=user_auth_headers,
        )
        response = client.post(
            "/api/subscriptions/",
            json={
                "publication_id": sample_publication.id,
                "duration_months": 1,
                "auto_renew": False,
            },
            headers=user_auth_headers,
        )
        assert response.status_code == 400
        assert "Active subscription already exists" in response.json()["detail"]


class TestSubscriptionList:
    def test_my_subscriptions_returns_owned(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        client.post(
            "/api/subscriptions/",
            json={
                "publication_id": sample_publication.id,
                "duration_months": 3,
                "auto_renew": False,
            },
            headers=user_auth_headers,
        )
        response = client.get("/api/subscriptions/my", headers=user_auth_headers)
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["publication_id"] == sample_publication.id


class TestSubscriptionCancel:
    """
    Чек-лист 9 — отмена подписки.
    """

    def test_cancel_active_subscription(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        created = client.post(
            "/api/subscriptions/",
            json={
                "publication_id": sample_publication.id,
                "duration_months": 1,
                "auto_renew": False,
            },
            headers=user_auth_headers,
        ).json()

        response = client.delete(
            f"/api/subscriptions/{created['id']}", headers=user_auth_headers
        )
        assert response.status_code == 204

        my = client.get("/api/subscriptions/my", headers=user_auth_headers).json()
        assert my[0]["status"] == "cancelled"

    def test_cancel_already_cancelled_rejected(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        created = client.post(
            "/api/subscriptions/",
            json={
                "publication_id": sample_publication.id,
                "duration_months": 1,
                "auto_renew": False,
            },
            headers=user_auth_headers,
        ).json()
        client.delete(f"/api/subscriptions/{created['id']}", headers=user_auth_headers)

        response = client.delete(
            f"/api/subscriptions/{created['id']}", headers=user_auth_headers
        )
        assert response.status_code == 400

    def test_cancel_nonexistent_subscription(self, client: TestClient, user_auth_headers):
        response = client.delete("/api/subscriptions/999999", headers=user_auth_headers)
        assert response.status_code == 404
