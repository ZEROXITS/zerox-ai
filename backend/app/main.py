from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pathlib import Path
import time

from app.config import settings
from app.models import init_db
from app.routers import auth_router, chat_router, models_router, admin_router
from app.routers.plugins import router as plugins_router
from app.routers.documents import router as documents_router
from app.routers.workspaces import router as workspaces_router
from app.routers.developer import router as developer_router
from app.routers.export import router as export_router

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create upload directories
Path("uploads/documents").mkdir(parents=True, exist_ok=True)
Path("uploads/attachments").mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("🚀 ZeroX AI Platform v2.0 Started!")
    print("📚 Features: Plugins, RAG, Workspaces, Developer API")
    yield
    # Shutdown
    print("👋 ZeroX AI Platform Shutting Down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    # 🤖 ZeroX AI Platform v2.0
    
    Advanced AI Chat Platform with Enterprise Features
    
    ## ✨ Features
    
    - **🧠 Multiple AI Models** - Llama 3.1, Mixtral, Gemma (via Groq)
    - **🔌 Plugins System** - Web search, Calculator, Weather, Wikipedia, Code execution
    - **📚 RAG (Document Chat)** - Upload PDFs, DOCX, and chat with your documents
    - **👥 Workspaces** - Team collaboration with shared conversations
    - **🔑 Developer API** - OpenAI-compatible API for developers
    - **📤 Export** - Export conversations as JSON, Markdown, HTML
    - **🔐 Security** - JWT auth, rate limiting, encrypted API keys
    
    ## 🚀 Quick Start
    
    1. Register at `/api/v1/auth/register`
    2. Login at `/api/v1/auth/login`
    3. Start chatting at `/api/v1/chat/`
    
    ## 📖 API Documentation
    
    - Swagger UI: `/docs`
    - ReDoc: `/redoc`
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include routers - Core
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

# Include routers - New Features
app.include_router(plugins_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")
app.include_router(developer_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "message": "Welcome to ZeroX AI Platform v2.0! 🤖",
        "features": [
            "Multi-model AI Chat",
            "Plugins (Web Search, Calculator, Weather, etc.)",
            "RAG - Chat with Documents",
            "Team Workspaces",
            "Developer API",
            "Export (JSON, Markdown, HTML)"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "database": "connected",
            "ai": "ready",
            "plugins": "active"
        }
    }

@app.get("/api/v1/features")
async def list_features():
    """List all available features"""
    return {
        "core": {
            "chat": "AI chat with multiple models",
            "auth": "JWT authentication with refresh tokens",
            "models": "Llama 3.1, Mixtral, Gemma"
        },
        "plugins": {
            "web_search": "Search the web",
            "calculator": "Mathematical calculations",
            "weather": "Weather information",
            "wikipedia": "Wikipedia search",
            "code_executor": "Execute Python code",
            "url_summarizer": "Summarize web pages",
            "translator": "Translate text"
        },
        "documents": {
            "upload": "Upload PDF, DOCX, TXT, CSV, JSON",
            "rag": "Chat with your documents",
            "search": "Semantic search in documents"
        },
        "collaboration": {
            "workspaces": "Team workspaces",
            "sharing": "Share conversations"
        },
        "developer": {
            "api_keys": "Generate API keys",
            "openai_compatible": "OpenAI-compatible endpoints"
        },
        "export": {
            "formats": ["JSON", "Markdown", "HTML", "Text"],
            "gdpr": "Export all user data"
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
