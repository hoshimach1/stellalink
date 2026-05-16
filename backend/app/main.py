import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine
from app.models.settings import AppSetting
from app.redis import close_redis, get_redis
from app.routers import admin, auth, profile

logger = logging.getLogger(__name__)


async def ensure_runtime_tables() -> None:
    for attempt in range(30):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: AppSetting.__table__.create(sync_conn, checkfirst=True))
            return
        except OSError:
            if attempt == 29:
                raise
            logger.warning("Database is not ready yet, retrying startup check...")
            await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_runtime_tables()
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
app.include_router(admin.router)
app.include_router(profile.router)

_uploads = Path(__file__).parent.parent / "uploads"
_uploads.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads)), name="uploads")


@app.get("/health")
async def health():
    return {"status": "ok"}
