import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import (
    complaints,
    publications,
    reviews,
    subscriptions,
    uploads,
    users,
)

app = FastAPI(
    title="MagNews Subscription Marketplace API",
    description=(
        "REST API маркетплейса подписок MagNews. "
        "Сейчас на витрине — журналы, газеты и научные журналы; "
        "архитектура каталога расширяется на цифровой контент."
    ),
    version="1.1.0",
)

PRODUCTION_ORIGIN = os.getenv("PRODUCTION_ORIGIN", "http://localhost:5173")

origins = [
    PRODUCTION_ORIGIN
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files: cover image storage exposed under /static
UPLOAD_ROOT = Path(os.getenv("UPLOAD_ROOT", "/app/uploads"))
(UPLOAD_ROOT / "covers").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(UPLOAD_ROOT)), name="static")

# Include routers
app.include_router(users.router)
app.include_router(publications.router)
app.include_router(subscriptions.router)
app.include_router(complaints.router)
app.include_router(reviews.router)
app.include_router(uploads.router)

@app.get("/")
def root():
    return {
        "message": "Subscription Management API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
