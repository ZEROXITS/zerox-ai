"""
Workspaces Router - Team collaboration
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.database import get_db
from app.models.user import User, Workspace, workspace_members, Conversation
from app.routers.auth import get_current_user

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_model: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    is_active: bool
    default_model: str
    member_count: int
    created_at: str

    class Config:
        from_attributes = True


class MemberAdd(BaseModel):
    email: str
    role: str = "member"  # member, admin


class MemberResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    avatar_url: Optional[str]


@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workspace"""
    
    new_workspace = Workspace(
        name=workspace.name,
        description=workspace.description,
        owner_id=current_user.id
    )
    db.add(new_workspace)
    db.commit()
    db.refresh(new_workspace)
    
    # Add owner as member
    db.execute(
        workspace_members.insert().values(
            workspace_id=new_workspace.id,
            user_id=current_user.id,
            role="owner"
        )
    )
    db.commit()
    
    return WorkspaceResponse(
        id=new_workspace.id,
        name=new_workspace.name,
        description=new_workspace.description,
        owner_id=new_workspace.owner_id,
        is_active=new_workspace.is_active,
        default_model=new_workspace.default_model,
        member_count=1,
        created_at=new_workspace.created_at.isoformat()
    )


@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's workspaces"""
    
    # Get workspaces where user is a member
    workspaces = db.query(Workspace).join(
        workspace_members,
        Workspace.id == workspace_members.c.workspace_id
    ).filter(
        workspace_members.c.user_id == current_user.id,
        Workspace.is_active == True
    ).all()
    
    result = []
    for ws in workspaces:
        member_count = db.query(workspace_members).filter(
            workspace_members.c.workspace_id == ws.id
        ).count()
        
        result.append(WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            description=ws.description,
            owner_id=ws.owner_id,
            is_active=ws.is_active,
            default_model=ws.default_model,
            member_count=member_count,
            created_at=ws.created_at.isoformat()
        ))
    
    return result


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workspace details"""
    
    # Check if user is a member
    membership = db.query(workspace_members).filter(
        workspace_members.c.workspace_id == workspace_id,
        workspace_members.c.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    member_count = db.query(workspace_members).filter(
        workspace_members.c.workspace_id == workspace_id
    ).count()
    
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        is_active=workspace.is_active,
        default_model=workspace.default_model,
        member_count=member_count,
        created_at=workspace.created_at.isoformat()
    )


@router.put("/{workspace_id}")
async def update_workspace(
    workspace_id: int,
    update: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update workspace (owner/admin only)"""
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if user is owner or admin
    membership = db.query(workspace_members).filter(
        workspace_members.c.workspace_id == workspace_id,
        workspace_members.c.user_id == current_user.id,
        workspace_members.c.role.in_(["owner", "admin"])
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if update.name:
        workspace.name = update.name
    if update.description is not None:
        workspace.description = update.description
    if update.default_model:
        workspace.default_model = update.default_model
    
    db.commit()
    
    return {"success": True, "message": "Workspace updated"}


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete workspace (owner only)"""
    
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.owner_id == current_user.id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or not owner")
    
    # Soft delete
    workspace.is_active = False
    db.commit()
    
    return {"success": True, "message": "Workspace deleted"}


# Members management
@router.get("/{workspace_id}/members", response_model=List[MemberResponse])
async def list_members(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List workspace members"""
    
    # Check if user is a member
    membership = db.query(workspace_members).filter(
        workspace_members.c.workspace_id == workspace_id,
        workspace_members.c.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")
    
    # Get all members
    members = db.query(User, workspace_members.c.role).join(
        workspace_members,
        User.id == workspace_members.c.user_id
    ).filter(
        workspace_members.c.workspace_id == workspace_id
    ).all()
    
    return [
        MemberResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=role,
            avatar_url=user.avatar_url
        )
        for user, role in members
    ]


@router.post("/{workspace_id}/members")
async def add_member(
    workspace_id: int,
    member: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a member to workspace"""
    
    # Check if user is owner or admin
    membership = db.query(workspace_members).filter(
        workspace_members.c.workspace_id == workspace_id,
        workspace_members.c.user_id == current_user.id,
        workspace_members.c.role.in_(["owner", "admin"])
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Find user by email
    user = db.query(User).filter(User.email == member.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already a member
    existing = db.query(workspace_members).filter(
        workspace_members.c.workspace_id == workspace_id,
        workspace_members.c.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    # Add member
    db.execute(
        workspace_members.insert().values(
            workspace_id=workspace_id,
            user_id=user.id,
            role=member.role
        )
    )
    db.commit()
    
    return {"success": True, "message": f"Added {user.username} to workspace"}


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from workspace"""
    
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Can't remove owner
    if user_id == workspace.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove workspace owner")
    
    # Check if current user is owner or admin
    membership = db.query(workspace_members).filter(
        workspace_members.c.workspace_id == workspace_id,
        workspace_members.c.user_id == current_user.id,
        workspace_members.c.role.in_(["owner", "admin"])
    ).first()
    
    # Users can also remove themselves
    if not membership and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Remove member
    db.execute(
        workspace_members.delete().where(
            and_(
                workspace_members.c.workspace_id == workspace_id,
                workspace_members.c.user_id == user_id
            )
        )
    )
    db.commit()
    
    return {"success": True, "message": "Member removed"}


# Workspace conversations
@router.get("/{workspace_id}/conversations")
async def list_workspace_conversations(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List conversations in workspace"""
    
    # Check if user is a member
    membership = db.query(workspace_members).filter(
        workspace_members.c.workspace_id == workspace_id,
        workspace_members.c.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member")
    
    conversations = db.query(Conversation).filter(
        Conversation.workspace_id == workspace_id,
        Conversation.is_archived == False
    ).order_by(Conversation.updated_at.desc()).all()
    
    return [
        {
            "id": conv.id,
            "title": conv.title,
            "model": conv.model,
            "user_id": conv.user_id,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        }
        for conv in conversations
    ]
