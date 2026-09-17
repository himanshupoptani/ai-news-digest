from backend.app.routers.news import router as news_router
from backend.app.routers.digest import router as digest_router
from backend.app.routers.chat import router as chat_router
from backend.app.routers.intelligence import router as intelligence_router

__all__ = [
    "news_router",
    "digest_router",
    "chat_router",
    "intelligence_router",
]
