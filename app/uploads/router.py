from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import uuid
import aiofiles
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file."""
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image type")

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        await f.write(content)

    return {"filename": filename, "url": f"/uploads/{filename}"}


@router.post("/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file."""
    if file.content_type not in settings.ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="Invalid video type")

    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "mp4"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        await f.write(content)

    return {"filename": filename, "url": f"/uploads/{filename}"}


@router.delete("/{filename}")
async def delete_file(filename: str):
    """Delete an uploaded file."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")
