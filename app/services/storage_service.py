import uuid
from pathlib import Path
import aiofiles
from fastapi import UploadFile
from app.core.exceptions import ValidationException

# Default storage configuration
UPLOAD_DIR = Path("uploads")
DEFAULT_MAX_FILE_SIZE_MB = 5
DEFAULT_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


class StorageService:
    """
    Reusable local file storage service.
    Handles file validation, unique naming, async disk saving, and cleanup.
    """

    @staticmethod
    async def save_file(
        file: UploadFile,
        folder: str = "general",
        allowed_extensions: set[str] | None = None,
        max_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB,
    ) -> str:
        """
        Validates and saves an uploaded file to local disk.
        Returns the public URL path (e.g., '/media/products/uuid.jpg').
        """
        if not file.filename:
            raise ValidationException("File must have a valid filename")

        allowed_exts = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
        file_ext = Path(file.filename).suffix.lower()

        # 1. Validate file extension
        if file_ext not in allowed_exts:
            allowed_list = ", ".join(sorted(allowed_exts))
            raise ValidationException(
                f"Unsupported file type '{file_ext}'. Allowed types: {allowed_list}"
            )

        # 2. Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        max_bytes = max_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise ValidationException(
                f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum limit of {max_size_mb} MB"
            )

        # 3. Prepare destination directory (e.g. uploads/products)
        target_dir = UPLOAD_DIR / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        # 4. Generate unique filename to prevent overwriting and path traversal
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        destination = target_dir / unique_filename

        # 5. Async write file in chunks (memory-efficient)
        async with aiofiles.open(destination, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunk
                await buffer.write(chunk)

        # 6. Return accessible media URL
        return f"/media/{folder}/{unique_filename}"

    @staticmethod
    def delete_file(file_url: str) -> bool:
        """
        Deletes a file from the local storage given its media URL.
        Example file_url: '/media/products/abcd.jpg'
        """
        if not file_url or not file_url.startswith("/media/"):
            return False

        relative_path = file_url.removeprefix("/media/")
        file_path = UPLOAD_DIR / relative_path

        # Check if file exists safely within uploads directory
        try:
            if file_path.is_file():
                file_path.unlink()
                return True
        except OSError:
            return False

        return False
