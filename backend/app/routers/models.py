from fastapi import APIRouter, Depends
from typing import List
from app.schemas import ModelInfo, ModelsResponse
from app.utils import get_current_user
from app.models import User

router = APIRouter(prefix="/models", tags=["Models"])

# Available AI Models
AVAILABLE_MODELS = [
    ModelInfo(
        id="llama-3.1-70b-versatile",
        name="Llama 3.1 70B",
        provider="groq",
        description="Meta's most capable open model. Excellent for complex tasks, coding, and analysis.",
        max_tokens=8192,
        is_free=True
    ),
    ModelInfo(
        id="llama-3.1-8b-instant",
        name="Llama 3.1 8B Instant",
        provider="groq",
        description="Fast and efficient model for quick responses.",
        max_tokens=8192,
        is_free=True
    ),
    ModelInfo(
        id="mixtral-8x7b-32768",
        name="Mixtral 8x7B",
        provider="groq",
        description="Mistral's mixture of experts model. Great for diverse tasks.",
        max_tokens=32768,
        is_free=True
    ),
    ModelInfo(
        id="gemma2-9b-it",
        name="Gemma 2 9B",
        provider="groq",
        description="Google's efficient instruction-tuned model.",
        max_tokens=8192,
        is_free=True
    ),
    ModelInfo(
        id="llama-3.2-90b-vision-preview",
        name="Llama 3.2 90B Vision",
        provider="groq",
        description="Multimodal model with vision capabilities.",
        max_tokens=8192,
        is_free=True
    ),
]

@router.get("", response_model=ModelsResponse)
async def get_models(current_user: User = Depends(get_current_user)):
    """Get available AI models"""
    return ModelsResponse(models=AVAILABLE_MODELS)

@router.get("/free", response_model=ModelsResponse)
async def get_free_models():
    """Get free AI models (no auth required)"""
    free_models = [m for m in AVAILABLE_MODELS if m.is_free]
    return ModelsResponse(models=free_models)
