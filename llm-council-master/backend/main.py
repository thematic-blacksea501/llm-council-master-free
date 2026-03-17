"""FastAPI backend for LLM Council."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import conversations, messages

app = FastAPI(title="LLM Council API")

# Enable CORS for cloud/browser clients
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversations.router)
app.include_router(messages.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
