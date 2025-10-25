from celery import current_task
from .celery_app import celery_app
from .processors import DocumentProcessor, AudioProcessor, VideoProcessor
import sys
import os
from pathlib import Path

# Add libs to path
sys.path.append('/app')
from libs.common.database import SessionLocal
from libs.common.models import KnowledgeSource

@celery_app.task(bind=True)
def process_upload_task(self, source_id: str):
    """Process uploaded file asynchronously"""
    
    db = SessionLocal()
    try:
        # Get knowledge source
        knowledge_source = db.query(KnowledgeSource).filter(
            KnowledgeSource.source_id == source_id
        ).first()
        
        if not knowledge_source:
            raise Exception(f"Knowledge source {source_id} not found")
        
        # Update status to processing
        knowledge_source.status = "processing"
        db.commit()
        
        # Process based on file type
        processor = None
        if knowledge_source.type in ['pdf', 'docx', 'pptx', 'text']:
            processor = DocumentProcessor()
        elif knowledge_source.type == 'audio':
            processor = AudioProcessor()
        elif knowledge_source.type == 'video':
            processor = VideoProcessor()
        else:
            raise Exception(f"Unsupported file type: {knowledge_source.type}")
        
        # Process the file
        result = processor.process(
            file_path=knowledge_source.storage_path,
            source_id=source_id,
            persona_id=str(knowledge_source.persona_id),
            org_id=str(knowledge_source.org_id)
        )
        
        # Update knowledge source with results
        knowledge_source.status = "ready"
        knowledge_source.chunk_count = result.get("chunk_count", 0)
        db.commit()
        
        return {
            "status": "success",
            "chunk_count": result.get("chunk_count", 0),
            "message": "Processing completed successfully"
        }
        
    except Exception as e:
        # Update status to failed
        if 'knowledge_source' in locals():
            knowledge_source.status = "failed"
            knowledge_source.error_message = str(e)
            db.commit()
        
        # Re-raise for Celery to handle
        raise self.retry(exc=e, countdown=60, max_retries=3)
        
    finally:
        db.close()