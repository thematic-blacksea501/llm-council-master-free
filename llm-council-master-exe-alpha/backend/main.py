"""FastAPI backend for LLM Council."""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

# Set up static file serving for React frontend
if getattr(sys, 'frozen', False):
    # Running inside a PyInstaller bundle
    base_dir = sys._MEIPASS
else:
    # Running in ordinary Python environment
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

frontend_dist = os.path.join(base_dir, "frontend", "dist")

if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    async def root():
        """Health check endpoint."""
        return {"status": "ok", "service": "LLM Council API (Frontend not built)"}

if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    multiprocessing.freeze_support()
    uvicorn.run(app, host="0.0.0.0", port=8001)
