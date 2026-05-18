import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import users, publications, subscriptions, complaints, reviews

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

# Include routers
app.include_router(users.router)
app.include_router(publications.router)
app.include_router(subscriptions.router)
app.include_router(complaints.router)
app.include_router(reviews.router)

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
