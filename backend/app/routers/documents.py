"""
Documents Router - RAG document management
"""
import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.user import User, Document, DocumentChunk
from app.routers.auth import get_current_user
from app.services.rag_service import rag_service

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    'txt', 'md', 'pdf', 'docx', 'csv', 'json', 'html', 'xml'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class DocumentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: str

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    query: str
    document_ids: Optional[List[int]] = None
    top_k: int = 5


class QueryResult(BaseModel):
    content: str
    score: float
    document_id: str
    chunk_index: int


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    description: str = Form(None),
    workspace_id: int = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document for RAG"""
    
    # Validate file extension
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.{ext}"
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Create database record
    document = Document(
        user_id=current_user.id,
        workspace_id=workspace_id,
        name=file.filename,
        description=description,
        file_type=ext,
        file_path=str(file_path),
        file_size=len(content),
        status="processing"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process document asynchronously
    try:
        result = await rag_service.process_document(
            file_path=str(file_path),
            doc_id=str(document.id),
            file_type=ext,
            metadata={
                "filename": file.filename,
                "user_id": current_user.id
            }
        )
        
        if result["success"]:
            document.status = "completed"
            document.chunk_count = result["chunks"]
        else:
            document.status = "failed"
        
        db.commit()
        
        return {
            "success": result["success"],
            "document_id": document.id,
            "name": document.name,
            "chunks": result.get("chunks", 0),
            "status": document.status
        }
        
    except Exception as e:
        document.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    workspace_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's documents"""
    query = db.query(Document).filter(Document.user_id == current_user.id)
    
    if workspace_id:
        query = query.filter(Document.workspace_id == workspace_id)
    
    documents = query.order_by(Document.created_at.desc()).all()
    
    return [
        DocumentResponse(
            id=doc.id,
            name=doc.name,
            description=doc.description,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status,
            chunk_count=doc.chunk_count,
            created_at=doc.created_at.isoformat()
        )
        for doc in documents
    ]


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document details"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "name": document.name,
        "description": document.description,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "status": document.status,
        "chunk_count": document.chunk_count,
        "created_at": document.created_at.isoformat(),
        "metadata": document.metadata
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from vector store
    rag_service.delete_document(str(document_id))
    
    # Delete file
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"success": True, "message": "Document deleted"}


@router.post("/query")
async def query_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query documents using RAG"""
    
    # Get user's document IDs
    if request.document_ids:
        # Verify user owns these documents
        docs = db.query(Document).filter(
            Document.id.in_(request.document_ids),
            Document.user_id == current_user.id
        ).all()
        doc_ids = [str(d.id) for d in docs]
    else:
        # Use all user's documents
        docs = db.query(Document).filter(
            Document.user_id == current_user.id,
            Document.status == "completed"
        ).all()
        doc_ids = [str(d.id) for d in docs]
    
    if not doc_ids:
        return {"results": [], "context": ""}
    
    # Query
    results = await rag_service.query(
        query=request.query,
        doc_ids=doc_ids,
        top_k=request.top_k
    )
    
    # Get context
    context = await rag_service.get_context(
        query=request.query,
        doc_ids=doc_ids
    )
    
    return {
        "results": [
            {
                "content": r["content"],
                "score": r["score"],
                "document_id": r["doc_id"],
                "chunk_index": r["metadata"].get("chunk_index", 0)
            }
            for r in results
        ],
        "context": context
    }


@router.post("/chat")
async def chat_with_documents(
    query: str,
    document_ids: List[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with documents - combines RAG with AI"""
    from app.services.ai_service import ai_service
    
    # Get context from documents
    if document_ids:
        docs = db.query(Document).filter(
            Document.id.in_(document_ids),
            Document.user_id == current_user.id
        ).all()
        doc_ids = [str(d.id) for d in docs]
    else:
        docs = db.query(Document).filter(
            Document.user_id == current_user.id,
            Document.status == "completed"
        ).all()
        doc_ids = [str(d.id) for d in docs]
    
    context = ""
    if doc_ids:
        context = await rag_service.get_context(query, doc_ids)
    
    # Build prompt with context
    system_prompt = """You are a helpful assistant that answers questions based on the provided context.
If the context doesn't contain relevant information, say so.
Always cite which part of the context you're using."""
    
    if context:
        user_message = f"""Context from documents:
---
{context}
---

Question: {query}

Please answer based on the context above."""
    else:
        user_message = query
    
    # Get AI response
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    response = await ai_service.chat(messages)
    
    return {
        "answer": response.get("content", ""),
        "context_used": bool(context),
        "documents_searched": len(doc_ids)
    }
