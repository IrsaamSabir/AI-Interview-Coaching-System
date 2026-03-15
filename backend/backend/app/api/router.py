from fastapi import APIRouter
from app.api.v1.endpoints import cv
from app.api.v1.endpoints import interview_routes
api_router = APIRouter(prefix="/api/v1/endpoints")

api_router.include_router(cv.router, prefix="/cv", tags=["CV"])
api_router.include_router(interview_routes.router, prefix="/interview", tags=["Interview"])