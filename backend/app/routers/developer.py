"""
Developer API Router - Public API for developers
"""
import secrets
import hashlib
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.user import User, DeveloperAPIKey
from app.routers.auth import get_current_user
from app.services.ai_service import ai_service

router = APIRouter(prefix="/developer", tags=["developer"])


class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = ["chat"]
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    permissions: List[str]
    rate_limit: int
    daily_limit: int
    total_requests: int
    is_active: bool
    expires_at: Optional[str]
    created_at: str
    last_used: Optional[str]


class ChatRequest(BaseModel):
    messages: List[dict]
    model: str = "llama-3.1-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its hash"""
    key = f"zx_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, key_hash


async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> DeveloperAPIKey:
    """Verify API key and return the key object"""
    
    if not x_api_key.startswith("zx_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    api_key = db.query(DeveloperAPIKey).filter(
        DeveloperAPIKey.key_hash == key_hash,
        DeveloperAPIKey.is_active == True
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API key expired")
    
    # Update usage
    api_key.total_requests += 1
    api_key.last_used = datetime.utcnow()
    db.commit()
    
    return api_key


# API Key Management (requires user auth)
@router.post("/keys", response_model=dict)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    
    # Generate key
    key, key_hash = generate_api_key()
    
    # Calculate expiration
    expires_at = None
    if key_data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_days)
    
    # Create key record
    api_key = DeveloperAPIKey(
        user_id=current_user.id,
        name=key_data.name,
        key_hash=key_hash,
        key_prefix=key[:10],
        permissions=key_data.permissions,
        expires_at=expires_at
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return {
        "id": api_key.id,
        "name": api_key.name,
        "key": key,  # Only shown once!
        "key_prefix": api_key.key_prefix,
        "permissions": api_key.permissions,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "message": "Save this key! It won't be shown again."
    }


@router.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's API keys"""
    
    keys = db.query(DeveloperAPIKey).filter(
        DeveloperAPIKey.user_id == current_user.id
    ).order_by(DeveloperAPIKey.created_at.desc()).all()
    
    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            permissions=k.permissions or [],
            rate_limit=k.rate_limit,
            daily_limit=k.daily_limit,
            total_requests=k.total_requests,
            is_active=k.is_active,
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
            created_at=k.created_at.isoformat(),
            last_used=k.last_used.isoformat() if k.last_used else None
        )
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key"""
    
    api_key = db.query(DeveloperAPIKey).filter(
        DeveloperAPIKey.id == key_id,
        DeveloperAPIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(api_key)
    db.commit()
    
    return {"success": True, "message": "API key deleted"}


@router.put("/keys/{key_id}/revoke")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an API key"""
    
    api_key = db.query(DeveloperAPIKey).filter(
        DeveloperAPIKey.id == key_id,
        DeveloperAPIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.is_active = False
    db.commit()
    
    return {"success": True, "message": "API key revoked"}


# Public API Endpoints (requires API key)
@router.post("/v1/chat/completions")
async def api_chat(
    request: ChatRequest,
    api_key: DeveloperAPIKey = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """OpenAI-compatible chat completions endpoint"""
    
    # Check permission
    if "chat" not in (api_key.permissions or []):
        raise HTTPException(status_code=403, detail="Permission denied: chat")
    
    try:
        response = await ai_service.chat(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # Format as OpenAI-compatible response
        return {
            "id": f"chatcmpl-{secrets.token_hex(12)}",
            "object": "chat.completion",
            "created": int(datetime.utcnow().timestamp()),
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.get("content", "")
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": response.get("prompt_tokens", 0),
                "completion_tokens": response.get("completion_tokens", 0),
                "total_tokens": response.get("total_tokens", 0)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/models")
async def api_list_models(
    api_key: DeveloperAPIKey = Depends(verify_api_key)
):
    """List available models"""
    
    if "models" not in (api_key.permissions or []) and "chat" not in (api_key.permissions or []):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    models = ai_service.get_available_models()
    
    return {
        "object": "list",
        "data": [
            {
                "id": model["id"],
                "object": "model",
                "created": 1700000000,
                "owned_by": model.get("provider", "zerox"),
                "permission": [],
                "root": model["id"],
                "parent": None
            }
            for model in models
        ]
    }


# Usage & Stats
@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get API usage statistics"""
    
    keys = db.query(DeveloperAPIKey).filter(
        DeveloperAPIKey.user_id == current_user.id
    ).all()
    
    total_requests = sum(k.total_requests for k in keys)
    active_keys = sum(1 for k in keys if k.is_active)
    
    return {
        "total_requests": total_requests,
        "total_keys": len(keys),
        "active_keys": active_keys,
        "keys": [
            {
                "name": k.name,
                "requests": k.total_requests,
                "last_used": k.last_used.isoformat() if k.last_used else None
            }
            for k in keys
        ]
    }
