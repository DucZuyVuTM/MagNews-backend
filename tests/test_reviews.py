"""
Тестовый сценарий 13: Оставление отзыва о подписке (позитивный).
Чек-лист 13 — отображение отзыва в карточке подписки.
"""
from fastapi.testclient import TestClient


class TestReviewCreation:
    def test_user_can_leave_review(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        response = client.post(
            "/api/reviews/",
            headers=user_auth_headers,
            json={
                "publication_id": sample_publication.id,
                "rating": 5,
                "text": "Отличное издание",
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["rating"] == 5
        assert body["text"] == "Отличное издание"
        assert body["publication_id"] == sample_publication.id

    def test_review_must_be_in_one_to_five_range(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        response = client.post(
            "/api/reviews/",
            headers=user_auth_headers,
            json={"publication_id": sample_publication.id, "rating": 6},
        )
        assert response.status_code == 422

    def test_duplicate_review_rejected(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        payload = {
            "publication_id": sample_publication.id,
            "rating": 4,
            "text": "ok",
        }
        first = client.post("/api/reviews/", headers=user_auth_headers, json=payload)
        assert first.status_code == 201

        second = client.post("/api/reviews/", headers=user_auth_headers, json=payload)
        assert second.status_code == 400

    def test_review_on_unapproved_publication_rejected(
        self, client: TestClient, user_auth_headers, provider_auth_headers
    ):
        create = client.post(
            "/api/publications/",
            headers=provider_auth_headers,
            json={
                "title": "Pending Magazine",
                "type": "magazine",
                "price_monthly": 5.0,
                "price_yearly": 50.0,
            },
        )
        pub_id = create.json()["id"]
        response = client.post(
            "/api/reviews/",
            headers=user_auth_headers,
            json={"publication_id": pub_id, "rating": 5},
        )
        assert response.status_code == 404


class TestReviewListing:
    def test_list_reviews_returns_visible_records(
        self, client: TestClient, user_auth_headers, sample_publication
    ):
        client.post(
            "/api/reviews/",
            headers=user_auth_headers,
            json={
                "publication_id": sample_publication.id,
                "rating": 4,
                "text": "Хорошо",
            },
        )

        response = client.get(f"/api/reviews/publication/{sample_publication.id}")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["rating"] == 4

    def test_summary_returns_average_and_count(
        self,
        client: TestClient,
        user_auth_headers,
        admin_auth_headers,
        sample_publication,
    ):
        client.post(
            "/api/reviews/",
            headers=user_auth_headers,
            json={"publication_id": sample_publication.id, "rating": 5},
        )
        client.post(
            "/api/reviews/",
            headers=admin_auth_headers,
            json={"publication_id": sample_publication.id, "rating": 3},
        )

        response = client.get(
            f"/api/reviews/publication/{sample_publication.id}/summary"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["review_count"] == 2
        assert body["average_rating"] == 4.0

    def test_summary_empty_publication(self, client: TestClient, sample_publication):
        response = client.get(
            f"/api/reviews/publication/{sample_publication.id}/summary"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["review_count"] == 0
        assert body["average_rating"] is None
