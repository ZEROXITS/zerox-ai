from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
from typing import List
import json

from app.models import User, Conversation, Message, UserAPIKey, get_db
from app.schemas import (
    ChatRequest, ChatResponse, ConversationCreate, ConversationResponse,
    ConversationDetail, MessageResponse
)
from app.utils import get_current_user, decrypt_api_key
from app.services import AIService
from app.config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])

# Rate limits per role
RATE_LIMITS = {
    "user": 50,      # 50 messages per day
    "premium": 500,  # 500 messages per day
    "admin": 10000   # Unlimited practically
}

async def check_rate_limit(user: User, db: AsyncSession):
    """Check if user has exceeded daily rate limit"""
    today = date.today()
    
    # Reset daily count if new day
    if user.last_message_date is None or user.last_message_date.date() < today:
        user.daily_messages = 0
        user.last_message_date = datetime.utcnow()
        await db.commit()
    
    limit = RATE_LIMITS.get(user.role, 50)
    if user.daily_messages >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily message limit ({limit}) exceeded. Upgrade to premium for more."
        )

async def get_user_api_key(user: User, provider: str, db: AsyncSession) -> str:
    """Get user's API key for a provider, or use default"""
    result = await db.execute(
        select(UserAPIKey).where(
            UserAPIKey.user_id == user.id,
            UserAPIKey.provider == provider,
            UserAPIKey.is_active == True
        )
    )
    user_key = result.scalar_one_or_none()
    
    if user_key:
        return decrypt_api_key(user_key.encrypted_key)
    
    # Use default key from settings
    default_key = getattr(settings, f"{provider.upper()}_API_KEY", "")
    if not default_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No API key configured for {provider}. Please add your own key in settings."
        )
    return default_key

@router.post("/send")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get AI response"""
    
    # Check rate limit
    await check_rate_limit(current_user, db)
    
    # Get or create conversation
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
            model=request.model
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)
    
    # Get conversation history
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .limit(20)  # Last 20 messages for context
    )
    messages = result.scalars().all()
    
    # Format messages for AI
    ai_messages = [
        {"role": "system", "content": "You are ZeroX AI, a helpful, intelligent, and friendly AI assistant. You provide accurate, detailed, and thoughtful responses. You can help with coding, analysis, writing, math, and general questions. Always be respectful and professional."}
    ]
    for msg in messages:
        ai_messages.append({"role": msg.role, "content": msg.content})
    
    # Get API key and create AI service
    api_key = await get_user_api_key(current_user, "groq", db)
    ai_service = AIService(api_key=api_key, provider="groq")
    
    if request.stream:
        # Streaming response
        async def generate():
            full_response = ""
            try:
                async for chunk in await ai_service.chat_completion(
                    messages=ai_messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    stream=True
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # Save assistant message after streaming completes
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_response,
                    model_used=request.model
                )
                db.add(assistant_message)
                
                # Update user stats
                current_user.daily_messages += 1
                current_user.total_messages += 1
                current_user.last_message_date = datetime.utcnow()
                
                # Update conversation
                conversation.updated_at = datetime.utcnow()
                
                await db.commit()
                
                yield f"data: {json.dumps({'done': True, 'conversation_id': conversation.id})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    else:
        # Non-streaming response
        try:
            response = await ai_service.chat_completion(
                messages=ai_messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=False
            )
            
            ai_content = response["choices"][0]["message"]["content"]
            
            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=ai_content,
                model_used=request.model
            )
            db.add(assistant_message)
            
            # Update user stats
            current_user.daily_messages += 1
            current_user.total_messages += 1
            current_user.last_message_date = datetime.utcnow()
            
            await db.commit()
            await db.refresh(assistant_message)
            
            return ChatResponse(
                conversation_id=conversation.id,
                message=MessageResponse.model_validate(user_message),
                response=MessageResponse.model_validate(assistant_message)
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's conversations"""
    
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id, Conversation.is_archived == False)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    conversations = result.scalars().all()
    
    response = []
    for conv in conversations:
        # Get message count
        count_result = await db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conv.id)
        )
        message_count = count_result.scalar()
        
        conv_response = ConversationResponse.model_validate(conv)
        conv_response.message_count = message_count
        response.append(conv_response)
    
    return response

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation with messages"""
    
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    
    return ConversationDetail(
        **ConversationResponse.model_validate(conversation).model_dump(),
        messages=[MessageResponse.model_validate(m) for m in messages]
    )

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation"""
    
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    await db.commit()
    
    return {"message": "Conversation deleted"}

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation"""
    
    conversation = Conversation(
        user_id=current_user.id,
        title=data.title,
        model=data.model
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return ConversationResponse.model_validate(conversation)
