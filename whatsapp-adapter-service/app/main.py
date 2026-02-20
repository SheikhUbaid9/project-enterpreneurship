from fastapi import FastAPI


app = FastAPI(title="WhatsApp Adapter Stub", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/platforms")
async def platforms() -> dict:
    return {
        "platforms": [
            {
                "platform": "whatsapp",
                "connected": False,
                "status": "stub",
                "detail": "WhatsApp adapter is not implemented in MVP.",
            }
        ]
    }
