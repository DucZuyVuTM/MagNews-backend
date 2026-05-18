"""
Тестовый сценарий 11: Подача и обработка жалобы на поставщика (позитивный).
Чек-лист 13 — обработка жалобы.
"""
from fastapi.testclient import TestClient


class TestSubmitComplaint:
    """
    Шаг 1: пользователь подаёт жалобу на издание.
    Ожидаемый результат: жалоба создана со статусом `new`, у неё есть номер.
    """

    def test_user_can_submit_complaint(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        response = client.post(
            "/api/complaints/",
            json={
                "publication_id": sample_publication.id,
                "reason": "Inappropriate content",
                "description": "Detailed description of the issue",
            },
            headers=user_auth_headers,
        )
        assert response.status_code == 201, response.text
        data = response.json()
        assert data["status"] == "new"
        assert data["id"] > 0
        assert data["reason"] == "Inappropriate content"

    def test_complaint_requires_auth(self, client: TestClient, sample_publication):
        response = client.post(
            "/api/complaints/",
            json={"publication_id": sample_publication.id, "reason": "Spam"},
        )
        assert response.status_code == 401

    def test_complaint_on_missing_publication(self, client: TestClient, user_auth_headers):
        response = client.post(
            "/api/complaints/",
            json={"publication_id": 999999, "reason": "Test"},
            headers=user_auth_headers,
        )
        assert response.status_code == 404

    def test_complaint_validates_reason_length(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        response = client.post(
            "/api/complaints/",
            json={"publication_id": sample_publication.id, "reason": ""},
            headers=user_auth_headers,
        )
        assert response.status_code == 422


class TestComplaintListing:
    """
    Шаг 2: пользователь видит только свои жалобы; админ — все.
    """

    def test_user_sees_only_own_complaints(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        client.post(
            "/api/complaints/",
            json={"publication_id": sample_publication.id, "reason": "First"},
            headers=user_auth_headers,
        )
        response = client.get("/api/complaints/my", headers=user_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_admin_can_list_all(
        self,
        client: TestClient,
        user_auth_headers,
        admin_auth_headers,
        sample_publication,
    ):
        client.post(
            "/api/complaints/",
            json={"publication_id": sample_publication.id, "reason": "From user"},
            headers=user_auth_headers,
        )
        response = client.get("/api/complaints/", headers=admin_auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_user_cannot_list_all(self, client: TestClient, user_auth_headers):
        response = client.get("/api/complaints/", headers=user_auth_headers)
        assert response.status_code == 403


class TestComplaintResolution:
    """
    Шаг 3: админ переводит статус жалобы (resolved / rejected).
    Чек-лист 13 — изменение статуса.
    """

    def test_admin_resolves_complaint(
        self,
        client: TestClient,
        user_auth_headers,
        admin_auth_headers,
        sample_publication,
    ):
        created = client.post(
            "/api/complaints/",
            json={"publication_id": sample_publication.id, "reason": "Spam"},
            headers=user_auth_headers,
        ).json()

        response = client.patch(
            f"/api/complaints/{created['id']}/status",
            json={"status": "resolved", "resolution_note": "Refunded"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["resolution_note"] == "Refunded"

    def test_user_cannot_update_status(
        self,
        client: TestClient,
        user_auth_headers,
        sample_publication,
    ):
        created = client.post(
            "/api/complaints/",
            json={"publication_id": sample_publication.id, "reason": "Test"},
            headers=user_auth_headers,
        ).json()
        response = client.patch(
            f"/api/complaints/{created['id']}/status",
            json={"status": "resolved"},
            headers=user_auth_headers,
        )
        assert response.status_code == 403

    def test_invalid_status_rejected(
        self,
        client: TestClient,
        user_auth_headers,
        admin_auth_headers,
        sample_publication,
    ):
        created = client.post(
            "/api/complaints/",
            json={"publication_id": sample_publication.id, "reason": "Test"},
            headers=user_auth_headers,
        ).json()
        response = client.patch(
            f"/api/complaints/{created['id']}/status",
            json={"status": "not-a-real-status"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
