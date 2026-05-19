import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.routers import cv, interview, speech, hume
import src.models  # noqa: F401 — registers all ORM models on Base.metadata
from src.database.connection import engine, Base

app = FastAPI(title="AI Interview Coaching System")


# ── Startup: create tables if they don't exist ────────────────────────────────

@app.on_event("startup")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── Exception handler ─────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb      = traceback.format_exc()
    safe_tb = tb.encode("utf-8", errors="replace").decode("utf-8")
    print("=" * 60, flush=True)
    print("FULL ERROR TRACEBACK:", flush=True)
    print(safe_tb, flush=True)
    print("=" * 60, flush=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(cv.router,        prefix="/api/v1/cv",        tags=["CV"])
app.include_router(interview.router, prefix="/api/v1/interview", tags=["Interview"])
app.include_router(speech.router,    prefix="/api/v1/speech",    tags=["Speech"])
app.include_router(hume.router,      prefix="/api/v1/hume",      tags=["Hume"])
