import re
from typing import List, Optional, Any, Dict
from pydantic import validator, BaseModel
from email_validator import validate_email, EmailNotValidError
import magic
import os

# File type validation
ALLOWED_MIME_TYPES = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'text/plain': ['.txt'],
    'audio/mpeg': ['.mp3'],
    'audio/wav': ['.wav'],
    'audio/mp4': ['.m4a'],
    'video/mp4': ['.mp4'],
    'video/avi': ['.avi'],
    'model/gltf+json': ['.gltf'],
    'model/gltf-binary': ['.glb'],
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png']
}

def validate_email_address(email: str) -> str:
    """Validate email address format"""
    try:
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError:
        raise ValueError("Invalid email address format")

def validate_password_strength(password: str) -> str:
    """Validate password strength"""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must contain at least one letter")
    
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one number")
    
    # Optional: require special characters
    # if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
    #     raise ValueError("Password must contain at least one special character")
    
    return password

def validate_file_type(file_content: bytes, filename: str) -> tuple[str, str]:
    """
    Validate file type based on content and filename
    
    Returns:
        (mime_type, file_extension)
    """
    
    # Get MIME type from content
    try:
        mime_type = magic.from_buffer(file_content, mime=True)
    except:
        # Fallback to filename extension
        mime_type = None
    
    # Get extension from filename
    file_extension = os.path.splitext(filename)[1].lower()
    
    # Validate against allowed types
    if mime_type in ALLOWED_MIME_TYPES:
        allowed_extensions = ALLOWED_MIME_TYPES[mime_type]
        if file_extension in allowed_extensions:
            return mime_type, file_extension
    
    # Check if extension is allowed (fallback)
    for allowed_mime, extensions in ALLOWED_MIME_TYPES.items():
        if file_extension in extensions:
            return allowed_mime, file_extension
    
    raise ValueError(f"File type not allowed: {mime_type or 'unknown'} ({file_extension})")

def validate_file_size(file_size: int, max_size: int = 100 * 1024 * 1024) -> int:
    """Validate file size (default max: 100MB)"""
    if file_size > max_size:
        raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)")
    return file_size

def validate_persona_name(name: str) -> str:
    """Validate persona name"""
    if not name or len(name.strip()) == 0:
        raise ValueError("Persona name cannot be empty")
    
    if len(name) > 255:
        raise ValueError("Persona name cannot exceed 255 characters")
    
    # Check for invalid characters
    if re.search(r'[<>"\']', name):
        raise ValueError("Persona name contains invalid characters")
    
    return name.strip()

def validate_organization_name(name: str) -> str:
    """Validate organization name"""
    if not name or len(name.strip()) == 0:
        raise ValueError("Organization name cannot be empty")
    
    if len(name) > 255:
        raise ValueError("Organization name cannot exceed 255 characters")
    
    # Check for invalid characters
    if re.search(r'[<>"\']', name):
        raise ValueError("Organization name contains invalid characters")
    
    return name.strip()

def validate_user_role(role: str) -> str:
    """Validate user role"""
    allowed_roles = ['admin', 'teacher', 'student', 'user']
    if role not in allowed_roles:
        raise ValueError(f"Invalid role. Must be one of: {', '.join(allowed_roles)}")
    return role

def validate_subscription_plan(plan: str) -> str:
    """Validate subscription plan"""
    allowed_plans = ['free', 'basic', 'pro', 'enterprise']
    if plan not in allowed_plans:
        raise ValueError(f"Invalid plan. Must be one of: {', '.join(allowed_plans)}")
    return plan

def validate_json_structure(data: Any, required_fields: List[str] = None) -> Dict:
    """Validate JSON structure"""
    if not isinstance(data, dict):
        raise ValueError("Data must be a JSON object")
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return data

def validate_uuid(uuid_string: str) -> str:
    """Validate UUID format"""
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'$',
        re.IGNORECASE
    )
    
    if not uuid_pattern.match(uuid_string):
        raise ValueError("Invalid UUID format")
    
    return uuid_string

def validate_url(url: str) -> str:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$'$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ValueError("Invalid URL format")
    
    return url

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove path separators and other dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def validate_animation_name(animation: str) -> str:
    """Validate 3D animation name"""
    allowed_animations = [
        'idle', 'talking', 'thinking', 'happy', 'sad', 'excited',
        'greeting', 'explaining', 'pointing', 'nodding', 'shaking_head', 'waving'
    ]
    
    if animation not in allowed_animations:
        raise ValueError(f"Invalid animation. Must be one of: {', '.join(allowed_animations)}")
    
    return animation

def validate_message_content(content: str) -> str:
    """Validate chat message content"""
    if not content or len(content.strip()) == 0:
        raise ValueError("Message content cannot be empty")
    
    if len(content) > 10000:  # 10KB limit
        raise ValueError("Message content too long (max 10,000 characters)")
    
    # Basic content filtering (extend as needed)
    if re.search(r'<script|javascript:|data:', content, re.IGNORECASE):
        raise ValueError("Message content contains potentially dangerous code")
    
    return content.strip()

# Pydantic validators for use in schemas
class ValidatedBaseModel(BaseModel):
    """Base model with common validators"""
    
    @validator('*', pre=True)
    def strip_strings(cls, v):
        """Strip whitespace from string fields"""
        if isinstance(v, str):
            return v.strip()
        return v

def create_length_validator(min_length: int = None, max_length: int = None):
    """Create a length validator for string fields"""
    def validator_func(cls, v):
        if isinstance(v, str):
            if min_length is not None and len(v) < min_length:
                raise ValueError(f'String too short (minimum {min_length} characters)')
            if max_length is not None and len(v) > max_length:
                raise ValueError(f'String too long (maximum {max_length} characters)')
        return v
    return validator_func