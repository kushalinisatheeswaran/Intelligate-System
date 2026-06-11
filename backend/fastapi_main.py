import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.websockets import router as websocket_router, alert_callback, gate_callback
from app.anpr.pipeline import ANPRPipeline
# Optional: import database session
# from app.database import async_session_maker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi_main")

# Initialize the global ANPR pipeline
# You can pass real database async session generators here
anpr_service = ANPRPipeline(
    camera_source=0, 
    db_session_func=None, # Replace with async_session_maker
    gate_callback=gate_callback,
    alert_callback=alert_callback
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the ANPR background service
    logger.info("Starting up FastAPI application...")
    await anpr_service.start()
    
    yield
    
    # Shutdown: Stop the ANPR background service
    logger.info("Shutting down FastAPI application...")
    await anpr_service.stop()

app = FastAPI(title="Intelligate System", lifespan=lifespan)

# Register WebSocket routes
app.include_router(websocket_router)

@app.get("/")
def read_root():
    return {"message": "Intelligate System API is running."}

@app.get("/anpr/status")
def anpr_status():
    return {"running": anpr_service.is_running}
