from pydantic import BaseModel
from typing import Optional


class MediaUploadResponse(BaseModel):
    file_url: str
    filename: str
    content_type: Optional[str] = None
