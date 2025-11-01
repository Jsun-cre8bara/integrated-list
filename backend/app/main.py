from fastapi import FastAPI

from .api.routes import admin, auth, merchants, stamp_books
from .core.config import get_settings
from .database import Base, engine

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(stamp_books.router, prefix=settings.API_V1_STR)
app.include_router(merchants.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
