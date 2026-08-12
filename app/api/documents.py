from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.models.models import Document, User
from app.api.deps import get_current_user
from app.services.rag import process_and_store_document

router = APIRouter()

class DocumentResponse(BaseModel):
    id: int
    filename: str
    upload_date: datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(('.pdf', '.txt', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF, TXT, and DOCX files are supported")
        
    try:
        contents = await file.read()
        doc_id = await process_and_store_document(db, contents, file.filename, current_user.id)
        
        # Fetch the created document to return
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalars().first()
        return doc
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Document).where(Document.user_id == current_user.id))
    return result.scalars().all()

@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == current_user.id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted successfully"}
