"""
Тестовый сценарий 5: Просмотр каталога с поиском и фильтрацией (позитивный).
Чек-лист 5, 6 — каталог + поиск/фильтрация.
"""
import time
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import ModerationStatus, Publication, PublicationType


def _seed_publications(db_session: Session, count: int = 12):
    types = [
        PublicationType.MAGAZINE,
        PublicationType.NEWSPAPER,
        PublicationType.JOURNAL,
    ]
    publications = []
    for i in range(count):
        pub = Publication(
            title=f"Publication {i}",
            description=f"Description body {i} keyword-{i % 3}",
            type=types[i % 3],
            publisher=f"Publisher {i % 4}",
            frequency="monthly",
            price_monthly=10.0 + i,
            price_yearly=100.0 + i * 10,
            cover_image_url=None,
            is_visible=True,
            is_available=True,
            moderation_status=ModerationStatus.APPROVED,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(pub)
        publications.append(pub)
    db_session.commit()
    return publications


class TestCatalogListing:
    """
    Чек-лист 5 — просмотр каталога без авторизации.
    """

    def test_anonymous_user_can_view_catalog(self, client: TestClient, db_session):
        _seed_publications(db_session, count=10)
        response = client.get("/api/publications/")
        assert response.status_code == 200
        assert len(response.json()) >= 10

    def test_hidden_publications_are_excluded(self, client: TestClient, db_session):
        _seed_publications(db_session, count=3)
        hidden = Publication(
            title="Hidden one",
            description="should not appear",
            type=PublicationType.JOURNAL,
            price_monthly=1.0,
            price_yearly=10.0,
            is_visible=False,
            is_available=True,
            moderation_status=ModerationStatus.APPROVED,
        )
        db_session.add(hidden)
        db_session.commit()

        response = client.get("/api/publications/")
        titles = [p["title"] for p in response.json()]
        assert "Hidden one" not in titles


class TestCatalogSearch:
    """
    Чек-лист 6 — поиск по ключевому слову и фильтр по категории.
    Замер времени выполнения вокруг запроса.
    """

    def test_search_by_keyword_in_title(self, client: TestClient, db_session):
        _seed_publications(db_session, count=12)

        start = time.perf_counter()
        response = client.get("/api/publications/?q=Publication 1")
        elapsed = time.perf_counter() - start

        assert response.status_code == 200
        data = response.json()
        assert all("Publication 1" in p["title"] for p in data)
        assert elapsed < 1.0, f"Search took {elapsed:.3f}s, expected < 1.0s"

    def test_search_by_keyword_in_description(self, client: TestClient, db_session):
        _seed_publications(db_session, count=9)
        response = client.get("/api/publications/?q=keyword-2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all("keyword-2" in p["description"] for p in data)

    def test_filter_by_type(self, client: TestClient, db_session):
        _seed_publications(db_session, count=12)
        response = client.get("/api/publications/?type=newspaper")
        assert response.status_code == 200
        data = response.json()
        assert all(p["type"] == "newspaper" for p in data)
        assert len(data) >= 1

    def test_search_and_filter_combined(self, client: TestClient, db_session):
        _seed_publications(db_session, count=12)
        response = client.get("/api/publications/?q=Publisher&type=magazine")
        assert response.status_code == 200
        for p in response.json():
            assert p["type"] == "magazine"

    def test_pagination(self, client: TestClient, db_session):
        _seed_publications(db_session, count=12)
        response = client.get("/api/publications/?skip=0&limit=5")
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_empty_query_returns_full_list(self, client: TestClient, db_session):
        _seed_publications(db_session, count=4)
        response = client.get("/api/publications/?q=")
        assert response.status_code == 200
        assert len(response.json()) == 4
