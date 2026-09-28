
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import societies, listings, uploads
from .auth import router as auth_router

app = FastAPI(title="Society Haat - Haat + Seva", version="1.0.0")

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(societies.router, prefix="/api/societies", tags=["societies"])
app.include_router(listings.router, prefix="/api/listings", tags=["listings"])
app.include_router(uploads.router, prefix="/api/uploads", tags=["uploads"])

@app.get("/")
def root():
    return {"app": "Society Haat", "tabs": ["Haat", "Seva"], "societies": ["SEV2", "APCPTH", "ALP"], "cluster": "Greater Noida West 1-2km"}

@app.get("/health")
def health():
    return {"status": "ok", "plug_and_play": "60s add society"}
