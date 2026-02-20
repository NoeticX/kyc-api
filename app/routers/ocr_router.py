from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import logging
import os

from app.services.ocr_service import NIDOCRService
from app.models.schemas import OCRResponse, OCRResultResponse
from app.models.database_models import OCRResult
from app.database import get_db
from app.utils.file_utils import validate_and_save_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["OCR"])

# Initialize OCR service (singleton)
ocr_service = NIDOCRService()

# Ensure upload directory exists
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/extract-nid", response_model=OCRResponse)
async def extract_nid(
    file: UploadFile = File(..., description="NID card image (PNG/JPG)"),
    db: Session = Depends(get_db)
):
    """
    Extract Name, Date of Birth, and NID Number from ID card image.
    Returns 400 error if extraction fails for any field.
    """
    logger.info(f"Processing upload: {file.filename}")
    
    try:
        # Save and validate image
        file_path = await validate_and_save_image(file, UPLOAD_DIR)
        logger.debug(f"Saved image to: {file_path}")
        
        # Process with OCR
        result = ocr_service.process_image(file_path)
        
        # Cleanup uploaded file immediately
        try:
            os.remove(file_path)
            logger.debug(f"Cleaned up: {file_path}")
        except OSError:
            logger.warning(f"Could not delete temp file: {file_path}")
        
        # Handle extraction failure
        if not result["success"]:
            error_msg = result.get("error", "Unknown extraction error")
            logger.warning(f"Extraction failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Extraction failed: {error_msg}"
            )
        
        # Save to database
        db_record = OCRResult(
            name=result["name"],
            date_of_birth=result["date_of_birth"],
            nid_number=result["nid_number"]
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        logger.info(f"Successfully processed NID #{db_record.id}")
        
        return OCRResponse(
            name=result["name"],
            date_of_birth=result["date_of_birth"],
            nid_number=result["nid_number"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during processing"
        )

@router.get("/results/{result_id}", response_model=OCRResultResponse)
async def get_result(result_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific OCR result by ID"""
    result = db.query(OCRResult).filter(OCRResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result
