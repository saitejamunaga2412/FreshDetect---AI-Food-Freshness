from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import connect_db, close_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

from fastapi.staticfiles import StaticFiles
import os

if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    # This handles unexpected errors
    logger.error(f"Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Server error", "error": str(exc)}
    )

from fastapi import HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    # This maps FastAPI "detail" to Express-style "message"
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"], # Production domains here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.api.auth import router as auth_router
from app.api.inventory import router as inventory_router
from app.api.scanner import router as scanner_router
from app.api.dashboard import router as dashboard_router
from app.api.reports import router as reports_router
from app.api.notifications import router as notifications_router
from app.api.scan_history import router as scan_history_router
from app.api.health import router as health_router
from app.api.knowledge_base import router as knowledge_base_router
from app.api.admin import router as admin_router

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(inventory_router, prefix="/api/inventory", tags=["inventory"])
app.include_router(scanner_router, prefix="/api/scanner", tags=["scanner"])
app.include_router(scan_history_router, prefix="/api/scan-history", tags=["scan_history"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(reports_router, prefix="/api/reports", tags=["reports"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])
app.include_router(health_router, prefix="/api/health", tags=["health"])
app.include_router(knowledge_base_router, prefix="/api/knowledge-base", tags=["knowledge_base"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

@app.on_event("startup")
async def startup_db_client():
    logger.info("Connecting to MongoDB")
    connect_db()
    
    # Initialize indexes
    from app.core.database import get_db
    db = get_db()
    await db.users.create_index("email", unique=True)
    
    # Initialize FoodKeeper Service on startup to cache CSV
    from app.services.foodkeeper_service import FoodKeeperService
    logger.info("Initializing FoodKeeper dataset")
    FoodKeeperService()

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Closing MongoDB connection")
    close_db()

@app.get("/")
def root():
    return {"message": "Food Freshness API (FastAPI) is running"}
