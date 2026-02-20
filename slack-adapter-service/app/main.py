from fastapi import FastAPI


app = FastAPI(title="Slack Adapter Stub", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/platforms")
async def platforms() -> dict:
    return {
        "platforms": [
            {
                "platform": "slack",
                "connected": False,
                "status": "stub",
                "detail": "Slack adapter is not implemented in MVP.",
            }
        ]
    }
