import uvicorn
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    
    print("=" * 60)
    print("NID OCR API Server")
    print("=" * 60)
    print("\nStarting server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )