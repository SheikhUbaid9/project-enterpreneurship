from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import redis_client
from app.core.middleware import RequestLoggingMiddleware
from app.routers.mcp_router import router as mcp_router
from app.routers.rest_router import router as rest_router
from app.services.fastmcp_service import FastMCPRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.ping()
    registry = FastMCPRegistry(redis_provider=lambda: redis_client)
    app.state.fastmcp_registry = registry

    if registry.server is not None:
        if hasattr(registry.server, "sse_app"):
            app.mount("/mcp/fastmcp", registry.server.sse_app())
        elif hasattr(registry.server, "streamable_http_app"):
            app.mount("/mcp/fastmcp", registry.server.streamable_http_app())
    yield
    await redis_client.aclose()


app = FastAPI(
    title="MCP Gateway Service",
    version="1.0.0",
    description="Single-entry MCP gateway for multi-platform inbox adapters.",
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

app.include_router(rest_router)
app.include_router(mcp_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
