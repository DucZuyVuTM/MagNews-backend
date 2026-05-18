"""
Общие фикстуры для тестов API. Используется SQLite-БД in-file для изоляции
от продуктового PostgreSQL.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal, Base, engine, get_db
from app.models import (
    ModerationStatus,
    Publication,
    PublicationType,
    User,
    UserRole,
)
from app.auth import get_password_hash


@pytest.fixture
def db_session() -> Session:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def regular_user(db_session: Session) -> User:
    user = User(
        email="user@example.com",
        username="regular_user",
        full_name="Regular User",
        hashed_password=get_password_hash("RegularPass123"),
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        email="admin@example.com",
        username="admin_user",
        full_name="Admin User",
        hashed_password=get_password_hash("AdminPass123"),
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _login_token(client: TestClient, login: str, password: str) -> str:
    response = client.post(
        "/api/users/login",
        data={"login": login, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def user_token(client: TestClient, regular_user: User) -> str:
    return _login_token(client, regular_user.username, "RegularPass123")


@pytest.fixture
def admin_token(client: TestClient, admin_user: User) -> str:
    return _login_token(client, admin_user.username, "AdminPass123")


@pytest.fixture
def user_auth_headers(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_auth_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_publication(db_session: Session) -> Publication:
    pub = Publication(
        title="Sample Magazine",
        description="A sample magazine for tests",
        type=PublicationType.MAGAZINE,
        publisher="Test Publisher",
        frequency="monthly",
        price_monthly=10.0,
        price_yearly=100.0,
        cover_image_url=None,
        is_visible=True,
        is_available=True,
        moderation_status=ModerationStatus.APPROVED,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(pub)
    db_session.commit()
    db_session.refresh(pub)
    return pub


@pytest.fixture
def provider_user(db_session: Session) -> User:
    user = User(
        email="provider@example.com",
        username="provider_user",
        full_name="Provider Co",
        hashed_password=get_password_hash("ProviderPass123"),
        role=UserRole.PROVIDER,
        is_active=True,
        company_name="Provider LLC",
        inn="7700000000",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def provider_token(client: TestClient, provider_user: User) -> str:
    return _login_token(client, provider_user.username, "ProviderPass123")


@pytest.fixture
def provider_auth_headers(provider_token: str) -> dict:
    return {"Authorization": f"Bearer {provider_token}"}
