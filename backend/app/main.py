from fastapi import FastAPI

app = FastAPI(title="Assignment 1 API")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return the API health status."""
    return {"status": "ok"}
