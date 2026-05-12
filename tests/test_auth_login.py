"""
Тестирование API аутентификации - Тестовые сценарии для эндпоинта /api/users/login

Таблица test cases основана на разработанной методологии тестирования.
Каждый тестовый сценарий включает предусловия, шаги, ожидаемые результаты и результаты теста.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import User, UserRole
from app.auth import get_password_hash


@pytest.fixture
def db_session():
    """Создание и очистка тестовой БД"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Создание тестовый клиент с внедренной БД"""
    def override_get_db():
        yield db_session
    
    from app.database import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(db_session):
    """Создание тестового пользователя"""
    user = User(
        email="testuser@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("TestPassword123"),
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestLoginSuccess:
    """
    Тестовый сценарий: Успешный вход с корректными учетными данными
    Функция: Тестирование API аутентификации
    """
    
    def test_login_with_valid_username_and_password(self, client, test_user):
        """
        Шаг 1: Отправить POST запрос на /api/users/login с корректным username и password
        Ожидаемый результат: Получить JWT token в ответе (status_code=200)
        """
        response = client.post(
            "/api/users/login",
            data={
                "login": "testuser",
                "password": "TestPassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
    
    def test_login_with_valid_email_and_password(self, client, test_user):
        """
        Шаг 2: Отправить POST запрос на /api/users/login с корректным email и password
        Ожидаемый результат: Получить JWT token в ответе (status_code=200)
        """
        response = client.post(
            "/api/users/login",
            data={
                "login": "testuser@example.com",
                "password": "TestPassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestLoginInvalidCredentials:
    """
    Тестовый сценарий: Неудачная попытка входа с неправильными учетными данными
    Функция: Обработка ошибок аутентификации
    """
    
    def test_login_with_wrong_password(self, client, test_user):
        """
        Шаг 1: Отправить POST запрос с корректным username, но неверным password
        Ожидаемый результат: Получить ошибку 401 (Unauthorized)
        """
        response = client.post(
            "/api/users/login",
            data={
                "login": "testuser",
                "password": "WrongPassword123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_login_with_nonexistent_username(self, client):
        """
        Шаг 2: Отправить POST запрос с несуществующим username
        Ожидаемый результат: Получить ошибку 401 (Unauthorized)
        """
        response = client.post(
            "/api/users/login",
            data={
                "login": "nonexistent_user",
                "password": "AnyPassword123"
            }
        )
        
        assert response.status_code == 401
    
    def test_login_with_nonexistent_email(self, client):
        """
        Шаг 3: Отправить POST запрос с несуществующим email
        Ожидаемый результат: Получить ошибку 401 (Unauthorized)
        """
        response = client.post(
            "/api/users/login",
            data={
                "login": "nonexistent@example.com",
                "password": "AnyPassword123"
            }
        )
        
        assert response.status_code == 401


class TestLoginInactiveUser:
    """
    Тестовый сценарий: Попытка входа с деактивированного аккаунта
    Функция: Проверка статуса активности пользователя
    """
    
    def test_login_with_inactive_user(self, db_session, client):
        """
        Предусловие: Создать неактивного пользователя
        Шаг 1: Отправить POST запрос с учетными данными неактивного пользователя
        Ожидаемый результат: Получить ошибку 401 (Unauthorized)
        """
        inactive_user = User(
            email="inactive@example.com",
            username="inactive_user",
            full_name="Inactive User",
            hashed_password=get_password_hash("TestPassword123"),
            role=UserRole.USER,
            is_active=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        response = client.post(
            "/api/users/login",
            data={
                "login": "inactive_user",
                "password": "TestPassword123"
            }
        )
        
        assert response.status_code == 401


class TestLoginMissingFields:
    """
    Тестовый сценарий: Отправка запроса с отсутствующими полями
    Функция: Валидация входных данных
    """
    
    def test_login_without_login_field(self, client):
        """
        Шаг 1: Отправить POST запрос без поля 'login'
        Ожидаемый результат: Получить ошибку 422 (Unprocessable Entity)
        """
        response = client.post(
            "/api/users/login",
            data={"password": "TestPassword123"}
        )
        
        assert response.status_code == 422
    
    def test_login_without_password_field(self, client):
        """
        Шаг 2: Отправить POST запрос без поля 'password'
        Ожидаемый результат: Получить ошибку 422 (Unprocessable Entity)
        """
        response = client.post(
            "/api/users/login",
            data={"login": "testuser"}
        )
        
        assert response.status_code == 422
    
    def test_login_with_empty_fields(self, client):
        """
        Шаг 3: Отправить POST запрос с пустыми полями
        Ожидаемый результат: Получить ошибку 422 или 401
        """
        response = client.post(
            "/api/users/login",
            data={
                "login": "",
                "password": ""
            }
        )
        
        assert response.status_code in [422, 401]


class TestTokenValidation:
    """
    Тестовый сценарий: Проверка полученного JWT token
    Функция: Валидация формата и использования token
    """
    
    def test_returned_token_is_valid_jwt(self, client, test_user):
        """
        Шаг 1: Получить token от успешного входа
        Ожидаемый результат: Token имеет формат JWT (3 части разделены точками)
        """
        response = client.post(
            "/api/users/login",
            data={
                "login": "testuser",
                "password": "TestPassword123"
            }
        )
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # JWT должен содержать 3 части разделенные точками
        parts = token.split(".")
        assert len(parts) == 3
    
    def test_token_can_be_used_for_authenticated_requests(self, client, test_user):
        """
        Шаг 2: Использовать полученный token для запроса к защищенному эндпоинту
        Ожидаемый результат: Запрос успешен (status_code=200)
        """
        # Получить token
        login_response = client.post(
            "/api/users/login",
            data={
                "login": "testuser",
                "password": "TestPassword123"
            }
        )
        
        token = login_response.json()["access_token"]
        
        # Использовать token для доступа к защищенному эндпоинту
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"


class TestLoginResponseFormat:
    """
    Тестовый сценарий: Проверка формата ответа при успешном входе
    Функция: Валидация структуры JSON ответа
    """
    
    def test_login_response_contains_required_fields(self, client, test_user):
        """
        Шаг 1: Отправить успешный POST запрос на /api/users/login
        Ожидаемый результат: Ответ содержит поля 'access_token' и 'token_type'
        """
        response = client.post(
            "/api/users/login",
            data={
                "login": "testuser",
                "password": "TestPassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
    
    def test_login_response_does_not_contain_password(self, client, test_user):
        """
        Шаг 2: Проверить, что пароль не включен в ответ
        Ожидаемый резу��ьтат: Поле 'password' отсутствует в ответе
        """
        response = client.post(
            "/api/users/login",
            data={
                "login": "testuser",
                "password": "TestPassword123"
            }
        )
        
        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data


class TestMultipleLoginAttempts:
    """
    Тестовый сценарий: Несколько попыток входа подряд
    Функция: Проверка стабильности системы аутентификации
    """
    
    def test_multiple_successful_logins(self, client, test_user):
        """
        Шаг 1: Выполнить несколько успешных попыток входа с одним пользователем
        Ожидаемый результат: Каждая попытка успешна и возвращает валидный token
        """
        for i in range(3):
            response = client.post(
                "/api/users/login",
                data={
                    "login": "testuser",
                    "password": "TestPassword123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert len(data["access_token"]) > 0
    
    def test_different_tokens_on_each_login(self, client, test_user):
        """
        Шаг 2: Проверить, что каждый вход генерирует новый token
        Ожидаемый результат: Tokens различаются между попытками входа
        """
        tokens = []
        
        for i in range(2):
            response = client.post(
                "/api/users/login",
                data={
                    "login": "testuser",
                    "password": "TestPassword123"
                }
            )
            
            token = response.json()["access_token"]
            tokens.append(token)
        
        # Tokens должны быть разными (содержать разные временные метки)
        assert len(set(tokens)) == 2
