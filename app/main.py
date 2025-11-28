import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import users, publications, subscriptions

app = FastAPI(
    title="Subscription Management API",
    description="API для управления подписками на журналы и газеты",
    version="1.0.0"
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

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(users.router)
app.include_router(publications.router)
app.include_router(subscriptions.router)

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
