from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import AsyncSessionLocal, init_database
from app.core.middleware import RequestLoggingMiddleware
from app.routers.messages_router import router as messages_router
from app.routers.platforms_router import router as platforms_router
from app.services.mock_seed_service import seed_mock_messages


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_database()
    async with AsyncSessionLocal() as session:
        await seed_mock_messages(session)
    yield


app = FastAPI(
    title="Email Adapter Service",
    version="1.0.0",
    description="Email adapter with mock mode for Multi-Platform Inbox.",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.include_router(messages_router)
app.include_router(platforms_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
