from contextlib import asynccontextmanager

import uvicorn
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine, get_db
from app.integrations.redis import close_redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # shutdown
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["system"])
async def heath() -> dict:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }

@app.get("/health/db", tags=["system"])
async def health_db(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(text("SELECT 1"))
    return {"status": "ok", "db_result": result.scalar()}


def dev() -> None:
    uvicorn.run("app.main:app", reload=True)    