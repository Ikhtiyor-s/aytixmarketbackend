from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
import aiofiles
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Uploads papkasi - app/uploads ichida
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "files")
IMAGES_DIR = os.path.join(UPLOAD_DIR, "images")
VIDEOS_DIR = os.path.join(UPLOAD_DIR, "videos")

# Papkalarni yaratish
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file."""
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image type")

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(IMAGES_DIR, filename)

    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        await f.write(content)

    return {"filename": filename, "url": f"/uploads/images/{filename}"}


@router.post("/images")
async def upload_multiple_images(files: list[UploadFile] = File(...)):
    """Upload multiple image files."""
    urls = []

    for file in files:
        if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid image type: {file.filename}")

        # Generate unique filename
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(IMAGES_DIR, filename)

        # Save file
        async with aiofiles.open(filepath, "wb") as f:
            content = await file.read()
            if len(content) > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=400, detail=f"File too large: {file.filename}")
            await f.write(content)

        urls.append(f"/uploads/images/{filename}")

    return {"urls": urls}


@router.post("/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file."""
    if file.content_type not in settings.ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="Invalid video type")

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "mp4"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(VIDEOS_DIR, filename)

    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        await f.write(content)

    return {"filename": filename, "url": f"/uploads/videos/{filename}"}


@router.delete("/images/{filename}")
async def delete_image(filename: str):
    """Delete an uploaded image."""
    filepath = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"message": "Image deleted"}
    raise HTTPException(status_code=404, detail="Image not found")


@router.delete("/videos/{filename}")
async def delete_video(filename: str):
    """Delete an uploaded video."""
    filepath = os.path.join(VIDEOS_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"message": "Video deleted"}
    raise HTTPException(status_code=404, detail="Video not found")
