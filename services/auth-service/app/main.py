from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import sys
import os

# Add libs to path
sys.path.append('/app')
from libs.common.database import get_db, init_db
from libs.common.models import User, Organization
from libs.common.schemas import UserRegister, UserLogin, TokenResponse, UserResponse, OrganizationCreate
from libs.common.auth import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user
from libs.common.logging_config import setup_logging, get_logger
from libs.common.metrics import get_metrics, get_metrics_content_type
from libs.common.exceptions import handle_exceptions

app = FastAPI(
    title="Bwenge OS Auth Service",
    description="Authentication and user management service",
    version="1.0.0"
)

# Setup logging
setup_logging("auth-service")
logger = get_logger(__name__)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-service"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(get_metrics(), media_type=get_metrics_content_type())

@app.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create organization if provided
        org = None
        if user_data.org_name:
            org = Organization(name=user_data.org_name)
            db.add(org)
            db.flush()  # Get the org_id
        else:
            # Use default organization
            org = db.query(Organization).filter(Organization.name == "Default Organization").first()
            if not org:
                org = Organization(name="Default Organization")
                db.add(org)
                db.flush()
        
        # Create user
        hashed_password = hash_password(user_data.password)
        user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            org_id=org.org_id,
            role="admin" if user_data.org_name else "user"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create tokens
        token_data = {
            "sub": str(user.user_id),
            "email": user.email,
            "org_id": str(user.org_id),
            "role": user.role
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return tokens"""
    # Find user
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create tokens
    token_data = {
        "sub": str(user.user_id),
        "email": user.email,
        "org_id": str(user.org_id),
        "role": user.role
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token"""
    from libs.common.auth import verify_token
    
    try:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        token_data = {
            "sub": str(user.user_id),
            "email": user.email,
            "org_id": str(user.org_id),
            "role": user.role
        }
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    user_id = current_user.get("sub")
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        org_id=user.org_id,
        created_at=user.created_at
    )

@app.post("/orgs/{org_id}/invite")
async def invite_user(
    org_id: str,
    invite_data: UserRegister,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite user to organization"""
    # Check if current user has permission to invite
    if current_user.get("role") not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Check if organization exists and user belongs to it
    org = db.query(Organization).filter(Organization.org_id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    if current_user.get("org_id") != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot invite to different organization"
        )
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == invite_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        
        # Create invited user
        hashed_password = hash_password(invite_data.password)
        user = User(
            name=invite_data.name,
            email=invite_data.email,
            password_hash=hashed_password,
            org_id=org_id,
            role="user"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {"message": "User invited successfully", "user_id": user.user_id}
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

@app.get("/orgs/{org_id}/members")
async def list_org_members(
    org_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List organization members"""
    # Check if user belongs to organization
    if current_user.get("org_id") != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get all users in organization
    users = db.query(User).filter(User.org_id == org_id).all()
    
    return [
        {
            "user_id": str(user.user_id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        for user in users
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)