"""
Тестовый сценарий 1: Регистрация нового пользователя (позитивный).
Тестовый сценарий 2: Регистрация с занятой электронной почтой (негативный).
"""
from fastapi.testclient import TestClient


class TestRegisterSuccess:
    """
    Сценарий: создание учётной записи с корректными данными.
    Чек-лист 1 — позитивная регистрация.
    """

    def test_register_returns_201_and_user_payload(self, client: TestClient):
        payload = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "StrongPass123",
        }
        response = client.post("/api/users/register", json=payload)

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["username"] == payload["username"]
        assert data["is_active"] is True
        assert "id" in data and data["id"] > 0
        assert "hashed_password" not in data
        assert "password" not in data

    def test_registered_user_can_login(self, client: TestClient):
        client.post(
            "/api/users/register",
            json={
                "email": "loginable@example.com",
                "username": "loginable",
                "full_name": "Loginable User",
                "password": "ValidPass123",
            },
        )
        response = client.post(
            "/api/users/login",
            data={"login": "loginable", "password": "ValidPass123"},
        )
        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"


class TestRegisterDuplicate:
    """
    Сценарий: регистрация с уже занятой электронной почтой / логином.
    Чек-лист 2 — негативная регистрация.
    """

    def test_register_with_existing_email_rejected(self, client: TestClient, regular_user):
        payload = {
            "email": regular_user.email,
            "username": "another_username",
            "full_name": "Duplicate Email",
            "password": "ValidPass123",
        }
        response = client.post("/api/users/register", json=payload)

        assert response.status_code == 400
        assert "Email" in response.json()["detail"]

    def test_register_with_existing_username_rejected(self, client: TestClient, regular_user):
        payload = {
            "email": "different@example.com",
            "username": regular_user.username,
            "full_name": "Duplicate Username",
            "password": "ValidPass123",
        }
        response = client.post("/api/users/register", json=payload)

        assert response.status_code == 400
        assert "Username" in response.json()["detail"]


class TestRegisterValidation:
    """
    Сценарий: валидация входных данных формы регистрации.
    """

    def test_register_rejects_weak_password_no_uppercase(self, client: TestClient):
        response = client.post(
            "/api/users/register",
            json={
                "email": "weak@example.com",
                "username": "weakuser",
                "full_name": "Weak User",
                "password": "weakpass123",
            },
        )
        assert response.status_code == 400

    def test_register_rejects_invalid_email(self, client: TestClient):
        response = client.post(
            "/api/users/register",
            json={
                "email": "not-an-email",
                "username": "bademail",
                "full_name": "Bad Email",
                "password": "ValidPass123",
            },
        )
        assert response.status_code == 422
