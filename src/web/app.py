"""OmniTreasury AI — FastAPI web application.

Run with:
    python -m uvicorn src.web.app:app --reload

Then open http://localhost:8000 in your browser.

API documentation at http://localhost:8000/api/docs
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from src.web.routers import upload, processing, cases, audit, metrics

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
_STATIC = _HERE / "static"

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="OmniTreasury AI",
    description=(
        "AI-powered treasury payment intelligence. "
        "Upload SWIFT MT103, CSV, JSON, and PDF files and run the full "
        "compliance / FX / liquidity / risk / decision pipeline."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS — allow any local origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(upload.router,     prefix="/api", tags=["upload"])
app.include_router(processing.router, prefix="/api", tags=["processing"])
app.include_router(cases.router,      prefix="/api", tags=["cases"])
app.include_router(audit.router,      prefix="/api", tags=["audit"])
app.include_router(metrics.router,    prefix="/api", tags=["metrics"])

# ── Static files ───────────────────────────────────────────────────────────────
if _STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


# ── SPA entry point ────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    """Serve the main dashboard SPA."""
    html_path = _STATIC / "index.html"
    if not html_path.exists():
        return HTMLResponse(
            "<h1 style='font-family:sans-serif;padding:2rem'>index.html not found — "
            "ensure src/web/static/index.html exists.</h1>",
            status_code=500,
        )
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


# Catch-all: serve index for any unmatched GET so client-side routing works
@app.get("/{path:path}", response_class=HTMLResponse, include_in_schema=False)
async def spa_fallback(path: str):
    html_path = _STATIC / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("Not Found", status_code=404)
