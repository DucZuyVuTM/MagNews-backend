"""
Чек-лист 22 — Соответствие API стандарту REST и формату JSON.

Запросы и ответы должны соответствовать REST: использование HTTP-методов
GET/POST/PATCH/DELETE, корректные коды состояния, content-type application/json.
"""
from fastapi.testclient import TestClient


class TestRestContractRoot:
    def test_root_returns_json(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert isinstance(response.json(), dict)

    def test_health_returns_json(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert response.json() == {"status": "healthy"}


class TestRestContractUsers:
    def test_register_returns_json(self, client: TestClient):
        response = client.post(
            "/api/users/register",
            json={
                "email": "rest@example.com",
                "username": "rest_user",
                "full_name": "Rest",
                "password": "ValidPass123",
            },
        )
        assert response.status_code == 201
        assert response.headers["content-type"].startswith("application/json")

    def test_login_returns_json(self, client: TestClient, regular_user):
        response = client.post(
            "/api/users/login",
            data={"login": regular_user.username, "password": "RegularPass123"},
        )
        assert response.headers["content-type"].startswith("application/json")

    def test_me_returns_json(self, client: TestClient, user_auth_headers):
        response = client.get("/api/users/me", headers=user_auth_headers)
        assert response.headers["content-type"].startswith("application/json")


class TestRestContractPublications:
    def test_list_returns_json_array(self, client: TestClient, sample_publication):
        response = client.get("/api/publications/")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert isinstance(response.json(), list)


class TestRestContractStatusCodes:
    def test_404_for_missing_resource(self, client: TestClient, user_auth_headers):
        response = client.get("/api/publications/999999", headers=user_auth_headers)
        assert response.status_code == 404

    def test_401_for_protected_without_token(self, client: TestClient):
        response = client.get("/api/subscriptions/my")
        assert response.status_code == 401

    def test_422_for_validation(self, client: TestClient):
        response = client.post(
            "/api/users/register",
            json={"email": "not-an-email", "username": "x", "password": "y"},
        )
        assert response.status_code == 422
