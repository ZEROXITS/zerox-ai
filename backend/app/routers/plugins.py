"""
Plugins Router - API endpoints for plugins/tools
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.services.plugins import plugin_manager
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginExecuteRequest(BaseModel):
    plugin_name: str
    params: Dict[str, Any]


class PluginResponse(BaseModel):
    success: bool
    plugin: str
    result: Dict[str, Any]


@router.get("/")
async def list_plugins(current_user: User = Depends(get_current_user)):
    """List all available plugins"""
    return {
        "plugins": plugin_manager.list_plugins()
    }


@router.post("/execute", response_model=PluginResponse)
async def execute_plugin(
    request: PluginExecuteRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute a plugin"""
    result = await plugin_manager.execute(request.plugin_name, request.params)
    
    return PluginResponse(
        success=result.get("success", False),
        plugin=request.plugin_name,
        result=result
    )


@router.get("/{plugin_name}")
async def get_plugin_info(
    plugin_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get information about a specific plugin"""
    plugin = plugin_manager.get(plugin_name)
    
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return {
        "name": plugin.name,
        "display_name": plugin.display_name,
        "description": plugin.description,
        "icon": plugin.icon,
        "schema": plugin.get_schema()
    }


# Quick access endpoints for common plugins
@router.get("/tools/search")
async def web_search(
    q: str,
    max_results: int = 5,
    current_user: User = Depends(get_current_user)
):
    """Quick web search"""
    result = await plugin_manager.execute("web_search", {
        "query": q,
        "max_results": max_results
    })
    return result


@router.get("/tools/weather")
async def get_weather(
    location: str,
    current_user: User = Depends(get_current_user)
):
    """Quick weather lookup"""
    result = await plugin_manager.execute("weather", {"location": location})
    return result


@router.get("/tools/wiki")
async def wiki_search(
    q: str,
    current_user: User = Depends(get_current_user)
):
    """Quick Wikipedia search"""
    result = await plugin_manager.execute("wikipedia", {"query": q})
    return result


@router.post("/tools/calculate")
async def calculate(
    expression: str,
    current_user: User = Depends(get_current_user)
):
    """Quick calculation"""
    result = await plugin_manager.execute("calculator", {"expression": expression})
    return result
