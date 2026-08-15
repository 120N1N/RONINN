import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from backend.config import settings
from backend.api import routes, websocket, health, llm, preprocess, train
from backend.db.database import engine, Base
import logging
from logging.handlers import RotatingFileHandler
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.core.limiter import limiter

from backend.db import models
# Inisialisasi Tabel (Sebaiknya gunakan Alembic di Production)
if settings.APP_ENV != "production":
    Base.metadata.create_all(bind=engine)

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler("logs/corvus_api.log", maxBytes=5*1024*1024, backupCount=5)
    ]
)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# SlowAPI Rate Limiting Setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Ensure avatars directory exists
os.makedirs("uploads/avatars", exist_ok=True)
# Mount static folder for avatars
app.mount("/static/avatars", StaticFiles(directory="uploads/avatars"), name="avatars")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler for 404 Custom Page
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        # Check if the request is for an API endpoint
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=404, content={"detail": exc.detail})
        
        # Return a custom HTML page for browser 404s instead of JSON
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>404 - Corvus Not Found</title>
            <style>
                body {
                    margin: 0; padding: 0; background-color: #0f0f0f; color: #fff;
                    font-family: 'Inter', -apple-system, sans-serif;
                    display: flex; justify-content: center; align-items: center;
                    height: 100vh; text-align: center; overflow: hidden;
                }
                .container {
                    background: rgba(20, 20, 20, 0.8);
                    border: 1px solid rgba(220, 38, 38, 0.2);
                    padding: 3rem 4rem;
                    border-radius: 2rem;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 0 50px rgba(220, 38, 38, 0.1);
                    animation: fadeIn 1s ease-out;
                }
                h1 {
                    font-size: 6rem; font-weight: 900; font-style: italic;
                    margin: 0; color: #dc2626; letter-spacing: -0.05em;
                    text-shadow: 0 0 20px rgba(220, 38, 38, 0.5);
                }
                h2 {
                    font-size: 1.5rem; text-transform: uppercase; letter-spacing: 0.2em;
                    margin-top: -10px; color: #fff; font-weight: 800;
                }
                p {
                    color: #94a3b8; font-size: 0.9rem; font-weight: bold; margin: 2rem 0;
                    line-height: 1.6; max-width: 400px;
                }
                a {
                    display: inline-block; padding: 1rem 2rem; background: #dc2626;
                    color: #fff; text-decoration: none; font-weight: 800; font-size: 0.8rem;
                    text-transform: uppercase; letter-spacing: 0.1em; border-radius: 1rem;
                    transition: all 0.3s;
                }
                a:hover {
                    background: #fff; color: #7f1d1d;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>404</h1>
                <h2>Target Not Found</h2>
                <p>Anda mengakses URL Server Backend. Silakan kembali ke layar Antarmuka (UI).</p>
                <a href="http://localhost:3000/">Kembali ke Dashboard</a>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=404)
    
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# Sesuaikan Router dengan versi Inti (v1)
app.include_router(routes.router, prefix="/api", tags=["core"])
app.include_router(llm.router, prefix="/api", tags=["llm"])
app.include_router(preprocess.router, prefix="/api", tags=["ml"])
app.include_router(train.router, prefix="/api", tags=["ml"])
app.include_router(health.router, prefix="/api", tags=["system"])
app.include_router(websocket.router, prefix="/api", tags=["realtime"])

@app.on_event("startup")
async def startup_event():
    # Check dependencies (DB, Redis, Tools)
    logging.info("Corvus Backend starting up...")

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
