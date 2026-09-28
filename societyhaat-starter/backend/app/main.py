from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title="Society Haat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from .auth import router as auth_router
from .haat import router as haat_router
from .seva import router as seva_router

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(haat_router, prefix="/api/haat", tags=["haat"])
app.include_router(seva_router, prefix="/api/seva", tags=["seva"])

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
    return {"status":"ok","message":"Society Haat backend running"}

# Serve frontend if exists (for public hosting)
# Looks for societyhaat-web.html in project root
try:
    BASE = Path(__file__).parent.parent.parent
    if (BASE / "societyhaat-web.html").exists():
        app.mount("/", StaticFiles(directory=str(BASE), html=True), name="static")
except Exception as e:
    print(f"Static mount skipped: {e}")
