"""
Тестовый сценарий: блокировка подписки администратором.
Чек-лист 14 — блокировка подписки.
"""
from fastapi.testclient import TestClient


def _create_subscription(client: TestClient, headers, publication_id: int) -> int:
    response = client.post(
        "/api/subscriptions/",
        json={
            "publication_id": publication_id,
            "duration_months": 1,
            "auto_renew": True,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


class TestAdminBlocksSubscription:
    """
    Чек-лист 14 — статус подписки меняется на "blocked", auto-renew сбрасывается.
    """

    def test_admin_can_block_active_subscription(
        self,
        client: TestClient,
        user_auth_headers,
        admin_auth_headers,
        sample_publication,
    ):
        sub_id = _create_subscription(client, user_auth_headers, sample_publication.id)

        response = client.patch(
            f"/api/subscriptions/{sub_id}/block",
            json={"reason": "Violates terms of service"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "blocked"
        assert data["auto_renew"] is False

    def test_block_persists_in_user_subscriptions(
        self,
        client: TestClient,
        user_auth_headers,
        admin_auth_headers,
        sample_publication,
    ):
        sub_id = _create_subscription(client, user_auth_headers, sample_publication.id)
        client.patch(
            f"/api/subscriptions/{sub_id}/block",
            json={"reason": "Test"},
            headers=admin_auth_headers,
        )

        my = client.get("/api/subscriptions/my", headers=user_auth_headers).json()
        assert my[0]["status"] == "blocked"

    def test_regular_user_cannot_block(
        self,
        client: TestClient,
        user_auth_headers,
        sample_publication,
    ):
        sub_id = _create_subscription(client, user_auth_headers, sample_publication.id)

        response = client.patch(
            f"/api/subscriptions/{sub_id}/block",
            json={"reason": "trying to block"},
            headers=user_auth_headers,
        )
        assert response.status_code == 403

    def test_block_nonexistent_subscription(
        self, client: TestClient, admin_auth_headers
    ):
        response = client.patch(
            "/api/subscriptions/999999/block",
            json={"reason": "x"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_double_block_rejected(
        self,
        client: TestClient,
        user_auth_headers,
        admin_auth_headers,
        sample_publication,
    ):
        sub_id = _create_subscription(client, user_auth_headers, sample_publication.id)
        client.patch(
            f"/api/subscriptions/{sub_id}/block",
            json={"reason": "first"},
            headers=admin_auth_headers,
        )

        response = client.patch(
            f"/api/subscriptions/{sub_id}/block",
            json={"reason": "second"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
