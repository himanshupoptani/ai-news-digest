import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from backend.app.config import settings
from backend.app.routers import (
    news_router,
    digest_router,
    chat_router,
    intelligence_router,
)

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Major Academic Project: AI News Intelligence Platform with RAG, Rational Agent, and Trustworthy AI Controls.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets and Templates
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
static_dir = os.path.join(project_root, "frontend", "static")
templates_dir = os.path.join(project_root, "frontend", "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=templates_dir) if os.path.exists(templates_dir) else None

# Register API Routers
app.include_router(news_router)
app.include_router(digest_router)
app.include_router(chat_router)
app.include_router(intelligence_router)

@app.get("/api/health", tags=["System Health"])
def health_check():
    """Returns platform operational health and active configuration status."""
    return {
        "status": "online",
        "platform": settings.PROJECT_NAME,
        "app_mode": settings.APP_MODE,
        "environment": settings.ENVIRONMENT,
        "database": "connected (SQLite)",
        "offline_demo_ready": True
    }

@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
def serve_index_page(request: Request):
    """Serves the Single-Page Application (SPA) dashboard."""
    index_path = os.path.join(templates_dir, "index.html")
    if os.path.exists(index_path) and templates:
        return templates.TemplateResponse("index.html", {"request": request, "project_name": settings.PROJECT_NAME})
    return HTMLResponse(
        content=f"<h1>{settings.PROJECT_NAME} API Server is Online</h1><p>Visit <a href='/docs'>/docs</a> for Swagger UI.</p>"
    )
