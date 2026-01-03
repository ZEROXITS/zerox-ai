from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ============ Auth Schemas ============
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    daily_messages: int
    total_messages: int
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ============ Chat Schemas ============
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    
class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    tokens_used: int
    model_used: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Chat"
    model: Optional[str] = "llama-3.1-70b-versatile"

class ConversationResponse(BaseModel):
    id: int
    title: str
    model: str
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    message_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class ConversationDetail(ConversationResponse):
    messages: List[MessageResponse] = []

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[int] = None
    model: Optional[str] = "llama-3.1-70b-versatile"
    temperature: Optional[float] = Field(0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(4096, ge=1, le=8192)
    stream: Optional[bool] = True

class ChatResponse(BaseModel):
    conversation_id: int
    message: MessageResponse
    response: MessageResponse

# ============ API Key Schemas ============
class APIKeyCreate(BaseModel):
    provider: str = Field(..., pattern="^(groq|huggingface|openai)$")
    api_key: str

class APIKeyResponse(BaseModel):
    id: int
    provider: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ Admin Schemas ============
class UserAdminResponse(UserResponse):
    last_login: Optional[datetime]
    
class StatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_conversations: int
    total_messages: int
    messages_today: int

# ============ Model Schemas ============
class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    description: str
    max_tokens: int
    is_free: bool

class ModelsResponse(BaseModel):
    models: List[ModelInfo]
