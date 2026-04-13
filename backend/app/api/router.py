from fastapi import APIRouter
from app.api.v1.endpoints import cv
from app.api.v1.endpoints import interview_routes
from app.api.v1.endpoints import speech_routes
from app.api.v1.endpoints import hume_routes

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(cv.router,               prefix="/cv",        tags=["CV"])
api_router.include_router(interview_routes.router, prefix="/interview", tags=["Interview"])
api_router.include_router(speech_routes.router,    prefix="/speech",    tags=["Speech"])
api_router.include_router(hume_routes.router,      prefix="/hume",      tags=["Hume"])