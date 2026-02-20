from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OCRResponse(BaseModel):
    """Response model for OCR extraction"""
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    nid_number: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "MAHMUDUL ISLAM",
                "date_of_birth": "01 Dec 1973",
                "nid_number": "823242838601"
            }
        }

class OCRResultResponse(BaseModel):
    """Response model for database records"""
    id: int
    name: str
    date_of_birth: str
    nid_number: str
    created_at: datetime

    class Config:
        from_attributes = True