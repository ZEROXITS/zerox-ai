"""
Export Router - Export conversations in various formats
"""
import json
from io import BytesIO
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.user import User, Conversation, Message
from app.routers.auth import get_current_user

router = APIRouter(prefix="/export", tags=["export"])


def conversation_to_dict(conversation: Conversation, messages: list) -> dict:
    """Convert conversation to dictionary"""
    return {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "model_used": msg.model_used,
                "tokens_used": msg.tokens_used
            }
            for msg in messages
        ]
    }


def conversation_to_markdown(conversation: Conversation, messages: list) -> str:
    """Convert conversation to Markdown"""
    md = f"# {conversation.title}\n\n"
    md += f"**Model:** {conversation.model}\n"
    md += f"**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
    md += "---\n\n"
    
    for msg in messages:
        if msg.role == "user":
            md += f"## 👤 User\n\n{msg.content}\n\n"
        elif msg.role == "assistant":
            md += f"## 🤖 Assistant\n\n{msg.content}\n\n"
        elif msg.role == "system":
            md += f"## ⚙️ System\n\n{msg.content}\n\n"
        md += "---\n\n"
    
    return md


def conversation_to_text(conversation: Conversation, messages: list) -> str:
    """Convert conversation to plain text"""
    text = f"Title: {conversation.title}\n"
    text += f"Model: {conversation.model}\n"
    text += f"Date: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    text += "=" * 50 + "\n\n"
    
    for msg in messages:
        role = msg.role.upper()
        text += f"[{role}]\n{msg.content}\n\n"
        text += "-" * 30 + "\n\n"
    
    return text


def conversation_to_html(conversation: Conversation, messages: list) -> str:
    """Convert conversation to HTML"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{conversation.title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }}
        h1 {{ color: #00d9ff; }}
        .meta {{ color: #888; margin-bottom: 20px; }}
        .message {{
            margin: 20px 0;
            padding: 15px;
            border-radius: 10px;
        }}
        .user {{
            background: #16213e;
            border-left: 4px solid #00d9ff;
        }}
        .assistant {{
            background: #0f3460;
            border-left: 4px solid #e94560;
        }}
        .system {{
            background: #1a1a2e;
            border: 1px solid #333;
            font-style: italic;
        }}
        .role {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #00d9ff;
        }}
        .content {{
            white-space: pre-wrap;
            line-height: 1.6;
        }}
        pre {{
            background: #0d0d1a;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        code {{
            font-family: 'Fira Code', monospace;
        }}
    </style>
</head>
<body>
    <h1>{conversation.title}</h1>
    <div class="meta">
        <p>Model: {conversation.model}</p>
        <p>Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}</p>
    </div>
"""
    
    for msg in messages:
        role_display = {"user": "👤 User", "assistant": "🤖 Assistant", "system": "⚙️ System"}.get(msg.role, msg.role)
        html += f"""
    <div class="message {msg.role}">
        <div class="role">{role_display}</div>
        <div class="content">{msg.content}</div>
    </div>
"""
    
    html += """
</body>
</html>
"""
    return html


@router.get("/conversation/{conversation_id}")
async def export_conversation(
    conversation_id: int,
    format: str = "json",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export a single conversation"""
    
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    filename = f"conversation_{conversation_id}_{datetime.now().strftime('%Y%m%d')}"
    
    if format == "json":
        data = conversation_to_dict(conversation, messages)
        content = json.dumps(data, indent=2, ensure_ascii=False)
        media_type = "application/json"
        filename += ".json"
        
    elif format == "markdown" or format == "md":
        content = conversation_to_markdown(conversation, messages)
        media_type = "text/markdown"
        filename += ".md"
        
    elif format == "text" or format == "txt":
        content = conversation_to_text(conversation, messages)
        media_type = "text/plain"
        filename += ".txt"
        
    elif format == "html":
        content = conversation_to_html(conversation, messages)
        media_type = "text/html"
        filename += ".html"
        
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use: json, markdown, text, html")
    
    return StreamingResponse(
        BytesIO(content.encode('utf-8')),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/all")
async def export_all_conversations(
    format: str = "json",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all user's conversations"""
    
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).all()
    
    if not conversations:
        raise HTTPException(status_code=404, detail="No conversations found")
    
    filename = f"all_conversations_{datetime.now().strftime('%Y%m%d')}"
    
    if format == "json":
        data = {
            "exported_at": datetime.now().isoformat(),
            "total_conversations": len(conversations),
            "conversations": []
        }
        
        for conv in conversations:
            messages = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at).all()
            data["conversations"].append(conversation_to_dict(conv, messages))
        
        content = json.dumps(data, indent=2, ensure_ascii=False)
        media_type = "application/json"
        filename += ".json"
        
    elif format == "markdown" or format == "md":
        content = f"# All Conversations\n\nExported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        content += f"Total: {len(conversations)} conversations\n\n"
        content += "=" * 50 + "\n\n"
        
        for conv in conversations:
            messages = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at).all()
            content += conversation_to_markdown(conv, messages)
            content += "\n\n" + "=" * 50 + "\n\n"
        
        media_type = "text/markdown"
        filename += ".md"
        
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use: json, markdown")
    
    return StreamingResponse(
        BytesIO(content.encode('utf-8')),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/user-data")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all user data (GDPR compliance)"""
    
    # Get all conversations
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).all()
    
    conversations_data = []
    for conv in conversations:
        messages = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at).all()
        conversations_data.append(conversation_to_dict(conv, messages))
    
    data = {
        "exported_at": datetime.now().isoformat(),
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "created_at": current_user.created_at.isoformat(),
            "total_messages": current_user.total_messages,
            "language": current_user.language,
            "theme": current_user.theme
        },
        "statistics": {
            "total_conversations": len(conversations),
            "total_messages": sum(len(c["messages"]) for c in conversations_data)
        },
        "conversations": conversations_data
    }
    
    content = json.dumps(data, indent=2, ensure_ascii=False)
    filename = f"user_data_{current_user.username}_{datetime.now().strftime('%Y%m%d')}.json"
    
    return StreamingResponse(
        BytesIO(content.encode('utf-8')),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
