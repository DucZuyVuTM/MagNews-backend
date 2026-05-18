"""
Загрузка обложек публикаций в локальное файловое хранилище.
"""
import io

from fastapi.testclient import TestClient


def _png_bytes() -> bytes:
    # Magic header is enough — validation is on content-type, not content.
    return b"\x89PNG\r\n\x1a\nfake-payload"


class TestCoverUpload:
    def test_provider_uploads_png(
        self, client: TestClient, provider_auth_headers
    ):
        payload = _png_bytes()
        response = client.post(
            "/api/uploads/cover",
            headers=provider_auth_headers,
            files={"file": ("cover.png", payload, "image/png")},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["url"].startswith("/static/covers/")
        assert body["url"].endswith(".png")

    def test_admin_uploads_jpeg(
        self, client: TestClient, admin_auth_headers
    ):
        payload = b"\xff\xd8\xff\xe0fake-jpeg"
        response = client.post(
            "/api/uploads/cover",
            headers=admin_auth_headers,
            files={"file": ("cover.jpg", payload, "image/jpeg")},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["url"].endswith(".jpg")

    def test_regular_user_forbidden(
        self, client: TestClient, user_auth_headers
    ):
        response = client.post(
            "/api/uploads/cover",
            headers=user_auth_headers,
            files={"file": ("cover.png", b"x", "image/png")},
        )
        assert response.status_code == 403

    def test_anonymous_forbidden(self, client: TestClient):
        response = client.post(
            "/api/uploads/cover",
            files={"file": ("cover.png", b"x", "image/png")},
        )
        assert response.status_code == 401

    def test_unsupported_mime_rejected(
        self, client: TestClient, provider_auth_headers
    ):
        response = client.post(
            "/api/uploads/cover",
            headers=provider_auth_headers,
            files={"file": ("malware.exe", b"MZx", "application/x-msdownload")},
        )
        assert response.status_code == 400

    def test_empty_file_rejected(
        self, client: TestClient, provider_auth_headers
    ):
        response = client.post(
            "/api/uploads/cover",
            headers=provider_auth_headers,
            files={"file": ("empty.png", b"", "image/png")},
        )
        assert response.status_code == 400

    def test_too_large_file_rejected(
        self, client: TestClient, provider_auth_headers
    ):
        big_payload = b"\x00" * (5 * 1024 * 1024 + 1)
        response = client.post(
            "/api/uploads/cover",
            headers=provider_auth_headers,
            files={"file": ("big.png", big_payload, "image/png")},
        )
        assert response.status_code == 413
