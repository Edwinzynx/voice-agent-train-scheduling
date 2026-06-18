import uvicorn
from app.config import config_manager

if __name__ == "__main__":
    settings = config_manager.settings
    print(f"Starting Train Booking Voice Agent Backend on {settings.host}:{settings.port}...")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
