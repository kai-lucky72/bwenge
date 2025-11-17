from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
import sys
import os
import uuid
import aiofiles
from pathlib import Path

# Add libs to path
sys.path.append('/app')
from libs.common.database import get_db, init_db
from libs.common.models import KnowledgeSource
from libs.common.schemas import KnowledgeUploadResponse, KnowledgeStatusResponse
from libs.common.auth import get_current_user

from .celery_app import celery_app
from .tasks import process_upload_task

app = FastAPI(
    title="Bwenge OS Ingest Service",
    description="Knowledge ingestion and processing service",
    version="1.0.0"
)

# Upload directory
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ingest-service"}

@app.post("/knowledge/upload", response_model=KnowledgeUploadResponse)
async def upload_knowledge(
    file: UploadFile = File(...),
    persona_id: str = Form(...),
    title: str = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload knowledge file for processing"""
    
    # Validate file type
    allowed_types = {
        'application/pdf': 'pdf',
        'audio/mpeg': 'audio',
        'audio/wav': 'audio',
        'audio/mp4': 'audio',
        'video/mp4': 'video',
        'video/avi': 'video',
        'text/plain': 'text',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx'
    }
    
    file_type = allowed_types.get(file.content_type)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    storage_filename = f"{file_id}{file_extension}"
    storage_path = UPLOAD_DIR / storage_filename
    
    try:
        # Save file
        async with aiofiles.open(storage_path, 'wb') as f:
            content = await file.read()
            
            # Validate file size
            MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
                )
            
            await f.write(content)
        
        # Create knowledge source record
        knowledge_source = KnowledgeSource(
            org_id=current_user["org_id"],
            persona_id=persona_id,
            title=title or file.filename,
            type=file_type,
            status="pending",
            storage_path=str(storage_path),
            file_size=len(content)
        )
        
        db.add(knowledge_source)
        db.commit()
        db.refresh(knowledge_source)
        
        # Queue processing task
        process_upload_task.delay(str(knowledge_source.source_id))
        
        return KnowledgeUploadResponse(
            upload_id=knowledge_source.source_id,
            status="pending",
            message="File uploaded successfully and queued for processing"
        )
        
    except Exception as e:
        # Clean up file if database operation fails
        if storage_path.exists():
            storage_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/knowledge/{upload_id}/status", response_model=KnowledgeStatusResponse)
async def get_knowledge_status(
    upload_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get knowledge processing status"""
    
    knowledge_source = db.query(KnowledgeSource).filter(
        KnowledgeSource.source_id == upload_id,
        KnowledgeSource.org_id == current_user["org_id"]
    ).first()
    
    if not knowledge_source:
        raise HTTPException(
            status_code=404,
            detail="Knowledge source not found"
        )
    
    return KnowledgeStatusResponse(
        source_id=knowledge_source.source_id,
        title=knowledge_source.title,
        type=knowledge_source.type,
        status=knowledge_source.status,
        chunk_count=knowledge_source.chunk_count,
        error_message=knowledge_source.error_message,
        created_at=knowledge_source.created_at
    )

@app.delete("/knowledge/{source_id}")
async def delete_knowledge(
    source_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete knowledge source"""
    
    knowledge_source = db.query(KnowledgeSource).filter(
        KnowledgeSource.source_id == source_id,
        KnowledgeSource.org_id == current_user["org_id"]
    ).first()
    
    if not knowledge_source:
        raise HTTPException(
            status_code=404,
            detail="Knowledge source not found"
        )
    
    try:
        # Delete file
        if knowledge_source.storage_path and Path(knowledge_source.storage_path).exists():
            Path(knowledge_source.storage_path).unlink()
        
        # Delete from database
        db.delete(knowledge_source)
        db.commit()
        
        # Delete from vector database
        try:
            import weaviate
            weaviate_client = weaviate.Client(url=os.getenv("WEAVIATE_URL", "http://localhost:8080"))
            
            # Delete all chunks for this source
            weaviate_client.batch.delete_objects(
                class_name="KnowledgeChunk",
                where={
                    "path": ["source_id"],
                    "operator": "Equal",
                    "valueString": str(source_id)
                }
            )
        except Exception as e:
            # Log warning but don't fail the request
            print(f"Warning: Failed to delete vectors from Weaviate: {e}")
        
        return {"message": "Knowledge source deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Deletion failed: {str(e)}"
        )

@app.get("/knowledge/sources")
async def list_knowledge_sources(
    persona_id: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List knowledge sources for organization"""
    
    query = db.query(KnowledgeSource).filter(
        KnowledgeSource.org_id == current_user["org_id"]
    )
    
    if persona_id:
        query = query.filter(KnowledgeSource.persona_id == persona_id)
    
    sources = query.all()
    
    return [
        KnowledgeStatusResponse(
            source_id=source.source_id,
            title=source.title,
            type=source.type,
            status=source.status,
            chunk_count=source.chunk_count,
            error_message=source.error_message,
            created_at=source.created_at
        )
        for source in sources
    ]

@app.get("/workers/status")
async def get_worker_status():
    """Check Celery worker status"""
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        
        if not stats:
            return {
                "status": "no_workers",
                "workers": [],
                "worker_count": 0,
                "active_tasks": 0
            }
        
        active_task_count = sum(len(tasks) for tasks in (active or {}).values())
        
        return {
            "status": "healthy",
            "workers": list(stats.keys()),
            "worker_count": len(stats),
            "active_tasks": active_task_count,
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "workers": [],
            "worker_count": 0
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)