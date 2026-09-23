import uvicorn
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, Depends

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import get_db

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
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
async def check_db(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(text("SELECT 1"))    
    return {"db_result": result.scalar()}
    

def dev() -> None:
    uvicorn.run("app.main:app", reload=True)    