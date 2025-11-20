from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import sys
import os
import uuid
import aiofiles
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import hmac

# Add libs to path
sys.path.append('/app')
from libs.common.database import get_db, init_db
from libs.common.models import Model3D, Persona
from libs.common.schemas import Model3DResponse
from libs.common.auth import get_current_user

app = FastAPI(
    title="Bwenge OS 3D Service",
    description="3D model management and serving service",
    version="1.0.0"
)

# Assets directory
ASSETS_DIR = Path("/app/assets")
ASSETS_DIR.mkdir(exist_ok=True)

# Secret for signed URLs
URL_SECRET = os.getenv("URL_SECRET", "your-url-signing-secret")
if URL_SECRET == "your-url-signing-secret":
    import secrets
    URL_SECRET = secrets.token_urlsafe(32)
    print(f"WARNING: URL_SECRET not set, using generated secret: {URL_SECRET}")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "3d-service"}

@app.get("/3d/persona/{persona_id}", response_model=Model3DResponse)
async def get_3d_model(
    persona_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get 3D model for persona"""
    
    # Verify persona belongs to user's organization
    persona = db.query(Persona).filter(
        Persona.persona_id == persona_id,
        Persona.org_id == current_user["org_id"]
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Get 3D model
    model_3d = db.query(Model3D).filter(
        Model3D.persona_id == persona_id
    ).first()
    
    if not model_3d:
        # Return default model
        return Model3DResponse(
            model_url=generate_signed_url("default/avatar.gltf"),
            animations=["idle", "talking", "thinking", "happy", "greeting"],
            scale=1.0,
            bounding_box={"width": 1.0, "height": 2.0, "depth": 1.0},
            version="1.0",
            mime_type="model/gltf+json"
        )
    
    # Generate signed URL for the model
    signed_url = generate_signed_url(model_3d.model_url)
    
    return Model3DResponse(
        model_url=signed_url,
        animations=model_3d.animations,
        scale=model_3d.scale,
        bounding_box=model_3d.bounding_box,
        version=model_3d.version,
        mime_type=model_3d.mime_type
    )

@app.post("/3d/persona/{persona_id}/upload")
async def upload_3d_model(
    persona_id: str,
    file: UploadFile = File(...),
    name: str = Form(...),
    animations: str = Form("[]"),  # JSON string
    scale: float = Form(1.0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload 3D model for persona"""
    
    # Verify persona belongs to user's organization
    persona = db.query(Persona).filter(
        Persona.persona_id == persona_id,
        Persona.org_id == current_user["org_id"]
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Validate file type
    allowed_types = {
        'model/gltf+json': '.gltf',
        'model/gltf-binary': '.glb',
        'application/octet-stream': '.glb'  # Some browsers send this for .glb
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    try:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = allowed_types[file.content_type]
        storage_filename = f"{file_id}{file_extension}"
        storage_path = ASSETS_DIR / "models" / storage_filename
        
        # Create directory if it doesn't exist
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        async with aiofiles.open(storage_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Parse animations
        import json
        try:
            animations_list = json.loads(animations)
        except json.JSONDecodeError:
            animations_list = ["idle", "talking"]
        
        # Create or update 3D model record
        model_3d = db.query(Model3D).filter(
            Model3D.persona_id == persona_id
        ).first()
        
        if model_3d:
            # Update existing model
            # Delete old file
            old_path = ASSETS_DIR / model_3d.model_url
            if old_path.exists():
                old_path.unlink()
            
            model_3d.name = name
            model_3d.model_url = f"models/{storage_filename}"
            model_3d.animations = animations_list
            model_3d.scale = scale
            model_3d.mime_type = file.content_type
            model_3d.updated_at = datetime.utcnow()
        else:
            # Create new model
            model_3d = Model3D(
                persona_id=persona_id,
                name=name,
                model_url=f"models/{storage_filename}",
                animations=animations_list,
                scale=scale,
                bounding_box={"width": 1.0, "height": 2.0, "depth": 1.0},
                mime_type=file.content_type
            )
            db.add(model_3d)
        
        db.commit()
        db.refresh(model_3d)
        
        return {
            "message": "3D model uploaded successfully",
            "model_id": model_3d.model_id,
            "model_url": generate_signed_url(model_3d.model_url)
        }
        
    except Exception as e:
        # Clean up file if database operation fails
        if 'storage_path' in locals() and storage_path.exists():
            storage_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/assets/{file_path:path}")
async def serve_asset(
    file_path: str,
    signature: str,
    expires: int
):
    """Serve 3D asset with signed URL verification"""
    
    # Verify signature
    if not verify_signed_url(file_path, signature, expires):
        raise HTTPException(status_code=403, detail="Invalid or expired URL")
    
    # Check if file exists
    asset_path = ASSETS_DIR / file_path
    if not asset_path.exists() or not asset_path.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Determine content type
    content_type = "application/octet-stream"
    if file_path.endswith('.gltf'):
        content_type = "model/gltf+json"
    elif file_path.endswith('.glb'):
        content_type = "model/gltf-binary"
    elif file_path.endswith('.bin'):
        content_type = "application/octet-stream"
    elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        content_type = "image/jpeg"
    elif file_path.endswith('.png'):
        content_type = "image/png"
    
    return FileResponse(
        path=asset_path,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.delete("/3d/persona/{persona_id}")
async def delete_3d_model(
    persona_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete 3D model for persona"""
    
    # Verify persona belongs to user's organization
    persona = db.query(Persona).filter(
        Persona.persona_id == persona_id,
        Persona.org_id == current_user["org_id"]
    ).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    # Get 3D model
    model_3d = db.query(Model3D).filter(
        Model3D.persona_id == persona_id
    ).first()
    
    if not model_3d:
        raise HTTPException(status_code=404, detail="3D model not found")
    
    try:
        # Delete file
        asset_path = ASSETS_DIR / model_3d.model_url
        if asset_path.exists():
            asset_path.unlink()
        
        # Delete from database
        db.delete(model_3d)
        db.commit()
        
        return {"message": "3D model deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Deletion failed: {str(e)}"
        )

def generate_signed_url(file_path: str, ttl_hours: int = 1) -> str:
    """Generate signed URL for asset"""
    
    expires = int((datetime.utcnow() + timedelta(hours=ttl_hours)).timestamp())
    
    # Create signature
    message = f"{file_path}:{expires}"
    signature = hmac.new(
        URL_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    base_url = os.getenv("BASE_URL", "http://localhost:8005")
    return f"{base_url}/assets/{file_path}?signature={signature}&expires={expires}"

def verify_signed_url(file_path: str, signature: str, expires: int) -> bool:
    """Verify signed URL"""
    
    # Check expiration
    if datetime.utcnow().timestamp() > expires:
        return False
    
    # Verify signature
    message = f"{file_path}:{expires}"
    expected_signature = hmac.new(
        URL_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@app.get("/3d/animations")
async def list_available_animations():
    """List available animation types"""
    return {
        "animations": [
            "idle",
            "talking",
            "thinking",
            "happy",
            "sad",
            "excited",
            "greeting",
            "explaining",
            "pointing",
            "nodding",
            "shaking_head",
            "waving"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)