import os
import uvicorn
from backend.app.config import settings
from backend.app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT))
    host = os.environ.get("HOST", "0.0.0.0")
    is_prod = os.environ.get("ENVIRONMENT", settings.ENVIRONMENT) == "production"
    reload_mode = False if is_prod else settings.DEBUG

    print("================================================================")
    print(f"STARTING {settings.PROJECT_NAME.upper()}")
    print("================================================================")
    print(f"Server:           http://{host}:{port}")
    print(f"Active Mode:      {settings.APP_MODE.upper()}")
    print(f"Production:       {is_prod}")
    print("================================================================")
    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=reload_mode
    )
