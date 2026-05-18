"""
Чек-лист 24 — Защита от XSS.
Чек-лист 25 — Защита от CSRF.

XSS: серверная часть отдаёт текстовые поля как есть, экранирование —
ответственность фронта (React по умолчанию escape'ит). Сценарно проверяем,
что серверная часть принимает и возвращает skript-payload без выполнения.

CSRF: JWT-аутентификация через Authorization-заголовок не уязвима к CSRF
на cookies. Тест ниже — стаб, фиксирующий используемую модель токенов.
"""
import pytest
from fastapi.testclient import TestClient


XSS_PAYLOAD = "<script>alert('xss')</script>"


class TestXssEscaping:
    """
    Чек-лист 24 — Защита от XSS на стороне API.
    """

    def test_publication_description_stored_as_text(
        self,
        client: TestClient,
        admin_auth_headers,
    ):
        response = client.post(
            "/api/publications/",
            json={
                "title": "Safe Title",
                "description": XSS_PAYLOAD,
                "type": "magazine",
                "publisher": "Test",
                "frequency": "monthly",
                "price_monthly": 10.0,
                "price_yearly": 100.0,
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        # Поле сохранилось как обычный текст — выполнение JavaScript на стороне
        # API не происходит, экранирование — задача рендера на фронте.
        assert data["description"] == XSS_PAYLOAD

    def test_complaint_description_stored_as_text(
        self,
        client: TestClient,
        user_auth_headers,
        sample_publication,
    ):
        response = client.post(
            "/api/complaints/",
            json={
                "publication_id": sample_publication.id,
                "reason": "Test",
                "description": XSS_PAYLOAD,
            },
            headers=user_auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["description"] == XSS_PAYLOAD


class TestCsrfModel:
    """
    Чек-лист 25 — Защита от CSRF. JWT через Authorization-заголовок.
    """

    def test_protected_endpoint_requires_bearer_token(self, client: TestClient):
        # Запрос без Authorization-заголовка не проходит — CSRF-вектор через
        # cookies в этой модели отсутствует.
        response = client.get("/api/subscriptions/my")
        assert response.status_code == 401

    def test_invalid_bearer_token_rejected(self, client: TestClient):
        response = client.get(
            "/api/subscriptions/my",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code == 401

    @pytest.mark.skip(reason="No cookie-based session — CSRF check not applicable to JWT in Authorization header")
    def test_cookie_csrf_token_validation(self):
        ...
