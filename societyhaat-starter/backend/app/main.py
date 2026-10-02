from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import os

BASE_DIR = Path(__file__).parent.parent.parent  # societyhaat-starter root

app = FastAPI(title="Society Haat - HTTP Service", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
try:
    from .auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    print("✅ auth router loaded")
except Exception as e:
    print(f"❌ auth router failed: {e}")

try:
    from .haat import router as haat_router
    app.include_router(haat_router, prefix="/api/haat", tags=["haat"])
    print("✅ haat router loaded")
except Exception as e:
    print(f"❌ haat router failed: {e}")

try:
    from .seva import router as seva_router
    app.include_router(seva_router, prefix="/api/seva", tags=["seva"])
    print("✅ seva router loaded")
except Exception as e:
    print(f"❌ seva router failed: {e}")

@app.get("/api/societies")
def societies():
    return {
        "societies": [
            {"id":"sev2","name":"Supertech Eco Village 2","blocks":["A","B","C","D"]},
            {"id":"apcpth","name":"Amrapali Centurion Park Terrace Homes","blocks":["A","B","C"]},
            {"id":"alp","name":"Amrapali Leisure Park","blocks":["A","B","C"]}
        ],
        "count": 3
    }

@app.get("/api/health")
def health():
    return {"status":"ok","message":"Society Haat backend running on HTTP 8000","http":True}

@app.get("/")
def root():
    # Redirect to main web page
    html_path = BASE_DIR / "societyhaat-web.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"message":"Society Haat API running. Frontend files not found at root, but API is ok. Use /docs"}

# Serve all HTML files directly from root
@app.get("/{page}.html")
def serve_html(page: str):
    file_path = BASE_DIR / f"{page}.html"
    if file_path.exists():
        return FileResponse(str(file_path))
    # Try societyhaat prefix
    file_path2 = BASE_DIR / f"societyhaat-{page}.html"
    if file_path2.exists():
        return FileResponse(str(file_path2))
    return HTMLResponse(f"<h1>404 - {page}.html not found</h1><p>Available at {BASE_DIR}</p>", status_code=404)

# Mount static dir if exists (for images etc)
try:
    if (BASE_DIR / "static").exists():
        app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
except:
    pass
