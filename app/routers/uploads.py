import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..auth import get_current_user
from ..models import User, UserRole
from ..schemas import CoverUploadResponse
from ..services.file_storage import LocalFileStorage

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


def get_storage() -> LocalFileStorage:
    return LocalFileStorage()


@router.post(
    "/cover",
    response_model=CoverUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    storage: LocalFileStorage = Depends(get_storage),
):
    if current_user.role not in (UserRole.PROVIDER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User is deactivated")

    content = await file.read()
    url = storage.save_cover(
        fileobj=io.BytesIO(content),
        content_type=file.content_type or "",
        size=len(content),
    )
    return CoverUploadResponse(url=url)
