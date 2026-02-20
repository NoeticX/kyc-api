import os
import uuid
from fastapi import UploadFile, HTTPException
from PIL import Image
import io

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_and_save_image(file: UploadFile, upload_dir: str) -> str:
    """
    Validate and save uploaded image securely
    Returns absolute path to saved file
    """
    # Check extension
    ext = file.filename.split('.')[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read content
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large (max {MAX_FILE_SIZE//1024//1024}MB)"
        )
    
    # Validate image
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
        # Reopen for saving (verify closes the image)
        img = Image.open(io.BytesIO(contents))
        # Convert to RGB if needed (handles RGBA, etc.)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image: {str(e)}"
        )
    
    # Generate safe filename
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(upload_dir, filename)
    
    # Save image
    try:
        img.save(filepath, quality=95)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save image: {str(e)}"
        )
    
    return os.path.abspath(filepath)