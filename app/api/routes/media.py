from fastapi import APIRouter, UploadFile, File, Query, Request, Response, status
from app.schemas.response import StandardResponse
from app.schemas.media import MediaUploadResponse
from app.services.storage_service import StorageService
from app.core.exceptions import NotFoundException
from app.core.limiter import limiter

router = APIRouter(prefix="/media", tags=["Media"])


@router.post(
    "/upload",
    response_model=StandardResponse[MediaUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single file or image",
)
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    response: Response,
    file: UploadFile = File(..., description="The file/image to upload"),
    folder: str = Query(
        "general", description="Subfolder inside uploads (e.g. products, avatars)"
    ),
):

    file_url = await StorageService.save_file(file=file, folder=folder)

    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "File uploaded successfully",
        "data": {
            "file_url": file_url,
            "filename": file.filename,
            "content_type": file.content_type,
        },
    }


@router.delete(
    "",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete an uploaded file by its URL",
)
def delete_file(
    file_url: str = Query(
        ..., description="The media URL to delete (e.g. /media/products/uuid.jpg)"
    ),
):
    deleted = StorageService.delete_file(file_url)
    if not deleted:
        raise NotFoundException(f"File '{file_url}' not found or could not be deleted")

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "File deleted successfully",
        "data": {"file_url": file_url},
    }
