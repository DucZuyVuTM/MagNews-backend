"""
Тестовый сценарий 12: Защита от SQL-инъекций при входе (негативный).
Чек-лист 18 — защита от SQL-инъекций.

SQLAlchemy ORM использует параметризованные запросы, поэтому payload вида
`' OR 1=1 --` не должен привести к авторизации.
"""
import pytest
from fastapi.testclient import TestClient


SQLI_PAYLOADS = [
    "' OR 1=1 --",
    "admin' --",
    "' OR '1'='1",
    "1' OR '1' = '1",
    "'; DROP TABLE users; --",
    "\" OR \"\"=\"",
    "admin'/*",
]


@pytest.mark.parametrize("payload", SQLI_PAYLOADS)
class TestSqlInjectionLogin:
    """
    Все SQL-payload'ы должны быть отвергнуты как обычные неверные креды.
    """

    def test_sqli_in_login_field_rejected(
        self, client: TestClient, regular_user, payload
    ):
        response = client.post(
            "/api/users/login",
            data={"login": payload, "password": "RegularPass123"},
        )
        assert response.status_code == 401

    def test_sqli_in_password_field_rejected(
        self, client: TestClient, regular_user, payload
    ):
        response = client.post(
            "/api/users/login",
            data={"login": regular_user.username, "password": payload},
        )
        assert response.status_code == 401


class TestSqlInjectionInSearch:
    """
    Поиск по каталогу также должен пройти SQL-инъекцию без 500.
    """

    def test_sqli_in_search_query(self, client: TestClient, sample_publication):
        response = client.get(
            "/api/publications/", params={"q": "' OR 1=1 --"}
        )
        assert response.status_code == 200, response.text
        assert response.json() == [] or all(
            "' OR 1=1 --" in p["title"]
            or "' OR 1=1 --" in (p["description"] or "")
            or "' OR 1=1 --" in (p["publisher"] or "")
            for p in response.json()
        )

    def test_users_table_still_exists_after_attempt(
        self, client: TestClient, regular_user
    ):
        client.post(
            "/api/users/login",
            data={"login": "'; DROP TABLE users; --", "password": "x"},
        )
        response = client.post(
            "/api/users/login",
            data={"login": regular_user.username, "password": "RegularPass123"},
        )
        assert response.status_code == 200
