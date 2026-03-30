from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.redis import close_redis, get_redis
from app.routers import auth, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()   # warm up connection
    yield
    await close_redis()


app = FastAPI(title="Stellalink API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)

_uploads = Path("uploads")
_uploads.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads)), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}
