from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import AsyncSessionLocal, init_database
from app.core.middleware import RequestLoggingMiddleware
from app.routers.auth_router import router as auth_router
from app.routers.users_router import router as users_router
from app.services.seed_service import seed_users


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_database()
    async with AsyncSessionLocal() as session:
        await seed_users(session)
    yield


app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="OAuth2/JWT auth service with RBAC for Multi-Platform Inbox.",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
