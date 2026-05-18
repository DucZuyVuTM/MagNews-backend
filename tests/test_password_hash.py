"""
Чек-лист 20 — Хранение паролей.

Пароли хранятся только в виде bcrypt-хэша; продуктивный код не должен
сохранять и возвращать сырой пароль.
"""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User


class TestPasswordHashing:
    def test_registered_password_is_bcrypt(self, client: TestClient, db_session: Session):
        client.post(
            "/api/users/register",
            json={
                "email": "hashed@example.com",
                "username": "hashed_user",
                "full_name": "Hashed",
                "password": "SecretPass123",
            },
        )

        user = db_session.query(User).filter(User.email == "hashed@example.com").first()
        assert user is not None
        assert user.hashed_password.startswith("$2b$")
        assert "SecretPass123" not in user.hashed_password
        assert len(user.hashed_password) >= 60  # bcrypt-hash length

    def test_hash_differs_between_users_with_same_password(
        self, client: TestClient, db_session: Session
    ):
        for i, email in enumerate(["a@example.com", "b@example.com"]):
            client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "username": f"user_{i}",
                    "full_name": "Test",
                    "password": "SamePass123",
                },
            )

        users = db_session.query(User).filter(
            User.email.in_(["a@example.com", "b@example.com"])
        ).all()
        assert len(users) == 2
        assert users[0].hashed_password != users[1].hashed_password

    def test_login_response_never_contains_hash(
        self, client: TestClient, regular_user
    ):
        response = client.post(
            "/api/users/login",
            data={"login": regular_user.username, "password": "RegularPass123"},
        )
        body = response.json()
        assert "hashed_password" not in body
        assert "password" not in body

    def test_me_endpoint_never_contains_hash(
        self, client: TestClient, user_auth_headers
    ):
        response = client.get("/api/users/me", headers=user_auth_headers)
        body = response.json()
        assert "hashed_password" not in body
        assert "password" not in body
