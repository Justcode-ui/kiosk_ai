"""
KioskAI FastAPI Application
Main application entry point
"""
# Reload trigger 3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db, close_db
from app.api.routes import auth, customers, messages, orders, analytics, reviews, websocket, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting KioskAI...")
    await init_db()
    print("Database initialized")
    
    # Initialize Sentry if configured
    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=1.0 if settings.DEBUG else 0.1
        )
        print("Sentry monitoring initialized")
    
    yield
    
    # Shutdown
    print("Shutting down KioskAI...")
    await close_db()
    print("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered customer communication platform for medium-scale businesses",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(customers.router)
app.include_router(messages.router)
app.include_router(orders.router)
app.include_router(analytics.router)
app.include_router(reviews.router)
app.include_router(websocket.router)


@app.get("/api")
async def api_root():
    """Root API endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }

# Mount Frontend Static Files (Must be last to avoid overriding API routes)
import os
from fastapi.staticfiles import StaticFiles

# Calculate path to frontend relative to backend/app/main.py
# current file is backend/app/main.py
# we want ../../frontend
# Calculate path to frontend (Robust for both Local and Docker)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Local: .../backend/app/main.py -> 2 levels up to root (.../KIOSK AI)
# current_dir = .../backend/app
# dirname(current_dir) = .../backend
# dirname(dirname(current_dir)) = .../KIOSK AI
root_local = os.path.dirname(os.path.dirname(current_dir))

# Docker: /app/app/main.py -> 1 level up to root (/app)
# current_dir = /app/app
# dirname(current_dir) = /app
root_docker = os.path.dirname(current_dir)

# Determine which root contains the frontend directory
if os.path.exists(os.path.join(root_local, "frontend")):
    project_root = root_local
elif os.path.exists(os.path.join(root_docker, "frontend")):
    project_root = root_docker
else:
    # Fallback to current directory to help debug if still failing
    print(f"DEBUG: Frontend not found. Checked {root_local} and {root_docker}")
    project_root = current_dir

frontend_path = os.path.join(project_root, "frontend")

# Serve landing.html at root
from fastapi.responses import FileResponse

@app.get("/")
async def serve_landing():
    landing_path = os.path.join(frontend_path, "landing.html")
    if os.path.exists(landing_path):
        return FileResponse(landing_path)
    
    # Debug info for deployment
    return {
        "message": "Landing page not found",
        "searched_at": landing_path,
        "current_dir": os.getcwd(),
        "project_root": project_root,
        "contents_of_root": os.listdir(project_root) if os.path.exists(project_root) else "Root not found"
    }

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {frontend_path}")


if __name__ == "__main__":
    import uvicorn
    
    # Use PORT from environment or default to 8000 (needed for Render)
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG
    )
