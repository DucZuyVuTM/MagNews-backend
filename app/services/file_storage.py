import os
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException


ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_COVER_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class LocalFileStorage:
    """File-system-backed implementation of the cover storage contract.

    Designed as an isolated point so that the underlying storage (local disk,
    S3-compatible bucket, managed object storage) can be swapped without
    touching the routers.
    """

    def __init__(self, root_dir: str | None = None, public_prefix: str = "/static"):
        resolved_root = root_dir or os.getenv("UPLOAD_ROOT", "/app/uploads")
        self.root = Path(resolved_root)
        self.public_prefix = public_prefix.rstrip("/")
        (self.root / "covers").mkdir(parents=True, exist_ok=True)

    def save_cover(self, fileobj: BinaryIO, content_type: str, size: int) -> str:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported content type {content_type!r}",
            )
        if size > MAX_COVER_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="File is too large (max 5 MB)",
            )
        if size <= 0:
            raise HTTPException(status_code=400, detail="Empty file")

        extension = ALLOWED_CONTENT_TYPES[content_type]
        filename = f"{uuid.uuid4().hex}{extension}"
        target_path = self.root / "covers" / filename

        with target_path.open("wb") as out:
            fileobj.seek(0)
            out.write(fileobj.read())

        return f"{self.public_prefix}/covers/{filename}"
