from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json, os
from pathlib import Path

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
PENDING_FILE = DATA_DIR / "pending.json"

def load_json(file, default):
    if not file.exists():
        return default
    try:
        return json.loads(file.read_text())
    except:
        return default

def save_json(file, data):
    file.write_text(json.dumps(data, indent=2))

def load_whitelist(society_id):
    f = DATA_DIR / f"{society_id}_residents.json"
    if not f.exists():
        return None
    return load_json(f, [])

# KNOWN societies - fallback if societies.json missing (your case)
KNOWN_SOCIETIES = ["sev2", "apcpth", "alp", "atsv"]

class RegisterRequest(BaseModel):
    society_id: str
    flat: str
    name: str
    phone: str

class ApproveRequest(BaseModel):
    phone: str

@router.post("/register")
def register(req: RegisterRequest):
    # FIX: Try to load societies.json, but if missing use KNOWN list
    societies = load_json(DATA_DIR / "societies.json", None)
    if societies is None or len(societies) == 0:
        society_ids = KNOWN_SOCIETIES
    else:
        society_ids = [s["id"] for s in societies]

    if req.society_id not in society_ids:
        raise HTTPException(400, detail=f"Invalid society {req.society_id}. Valid: {', '.join(society_ids)}")

    whitelist = load_whitelist(req.society_id)
    if whitelist is not None and req.flat not in whitelist:
        raise HTTPException(403, detail=f"Denied: Flat {req.flat} not found in {req.society_id.upper()} whitelist. File: {req.society_id}_residents.json has {whitelist}. You are not resident of {req.society_id.upper()}. Please register in your own society.")

    users = load_json(USERS_FILE, [])
    pending = load_json(PENDING_FILE, [])

    if any(u["phone"] == req.phone for u in users):
        raise HTTPException(400, detail="Phone already registered - verified")
    if any(p["phone"] == req.phone for p in pending):
        raise HTTPException(400, detail="Already pending approval - wait for admin")

    if any(u["flat"] == req.flat and u["society_id"] == req.society_id for u in users):
        raise HTTPException(400, detail=f"Flat {req.flat} already registered in {req.society_id.upper()}")

    pending.append({
        "society_id": req.society_id,
        "flat": req.flat,
        "name": req.name,
        "phone": req.phone,
        "status": "pending"
    })
    save_json(PENDING_FILE, pending)

    return {"message": f"Registered for {req.society_id.upper()} - pending admin approval", "society_id": req.society_id, "flat": req.flat, "status": "pending"}

@router.get("/pending")
def get_pending():
    return {"pending": load_json(PENDING_FILE, [])}

@router.post("/approve")
def approve(req: ApproveRequest):
    pending = load_json(PENDING_FILE, [])
    users = load_json(USERS_FILE, [])

    found = next((p for p in pending if p["phone"] == req.phone), None)
    if not found:
        raise HTTPException(404, detail="Pending user not found")

    pending = [p for p in pending if p["phone"] != req.phone]
    found["status"] = "verified"
    users.append(found)

    save_json(PENDING_FILE, pending)
    save_json(USERS_FILE, users)

    return {"message": f"Approved {found['name']} for {found['society_id'].upper()} {found['flat']}", "user": found}

@router.get("/users")
def get_users():
    return {"users": load_json(USERS_FILE, [])}
