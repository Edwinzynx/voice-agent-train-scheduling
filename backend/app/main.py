import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import calls, dashboard, eval
from .config import configured_origins

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize DB tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception:
    # Never advertise a healthy service while calls cannot be persisted.
    logger.error("Database initialization failed. Check DATABASE_URL and database connectivity.")
    raise RuntimeError("Database initialization failed; refusing to start without call storage.") from None

app = FastAPI(
    title="Train Voice Agent Server",
    description="FastAPI WebSocket & HTTP server for FSM Train Voice Agent Dashboard",
    version="1.0"
)

# Enable CORS for frontend dashboard communication
import os
allowed_origins = configured_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(calls.router)
app.include_router(dashboard.router)
app.include_router(eval.router)

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "revision": os.getenv("RENDER_GIT_COMMIT", "development"),
        "speech_provider": "sarvam",
        "app": "Train Booking Voice Agent Backend",
        "docs_url": "/docs"
    }
