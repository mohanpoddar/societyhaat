
from fastapi import APIRouter, UploadFile, File
router = APIRouter()

# Multi-photo upload for cake etc - Production: saves to gs://haat-listing-images
@router.post("/image")
async def upload_image(file: UploadFile = File(...), listing_id: str = "demo"):
    # In production: upload to Cloud Storage gs://haat-listing-images/societies/{society_id}/{listing_id}/
    # Auto-resize to 800x800 + thumbnail 200x200 via Cloud Function
    return {
        "message": "Uploaded - will be resized to WebP 800x800 + thumb",
        "filename": file.filename,
        "size": "max 5MB, JPG/PNG",
        "max_photos": 5,
        "first_is_cover": True,
        "gcs_path": f"gs://haat-listing-images/societies/demo/{listing_id}/{file.filename}",
        "cdn_url": f"https://cdn.societyhaat.in/{listing_id}/{file.filename}.webp"
    }
