from fastapi import FastAPI,Depends
from app.api.router import api_router

app = FastAPI(title="AI Interview Coaching System")

app.include_router(api_router)


