from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from pathlib import Path
from uuid import uuid4

from ..services.transcript_analyzer import TranscriptAnalyzer
from ..core.config import settings

router = APIRouter(prefix="/transcript", tags=["transcript"])
analyzer = TranscriptAnalyzer()

# Ensure upload directory exists
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_transcript(file: UploadFile = File(...)):
    """Upload transcript PDF file"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Generate unique file ID
        file_id = str(uuid4())
        file_extension = ".pdf"
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{file_extension}")

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return JSONResponse(content={
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "message": "File uploaded successfully"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.post("/analyze")
async def analyze_transcript(file: UploadFile = File(...)):
    """Upload and analyze transcript in one step"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Generate unique file ID
        file_id = str(uuid4())
        file_extension = ".pdf"
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{file_extension}")

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Analyze transcript
        result = analyzer.analyze(file_path)

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing transcript: {str(e)}")


@router.get("/analyze/{file_id}")
async def analyze_uploaded_transcript(file_id: str):
    """Analyze previously uploaded transcript"""
    try:
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}.pdf")

        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Analyze transcript
        result = analyzer.analyze(file_path)

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing transcript: {str(e)}")
