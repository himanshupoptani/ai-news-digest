import uvicorn
from backend.app.config import settings
from backend.app.main import app

if __name__ == "__main__":
    print("================================================================")
    print(f"STARTING {settings.PROJECT_NAME.upper()}")
    print("================================================================")
    print(f"Local Server:     http://{settings.HOST}:{settings.PORT}")
    print(f"Swagger API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Active Mode:      {settings.APP_MODE.upper()}")
    print("================================================================")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
