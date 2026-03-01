from fastapi import APIRouter
from app.api.routes import health, query, emendas, parlamentares

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(query.router, tags=["query"])
api_router.include_router(emendas.router, tags=["emendas"])
api_router.include_router(parlamentares.router, tags=["parlamentares"])
