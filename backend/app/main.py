import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import calls, dashboard, eval

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
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

app = FastAPI(
    title="Train Voice Agent Server",
    description="FastAPI WebSocket & HTTP server for FSM Train Voice Agent Dashboard",
    version="1.0"
)

# Enable CORS for frontend dashboard communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend origin
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
        "app": "Train Booking Voice Agent Backend",
        "docs_url": "/docs"
    }
