from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from datetime import datetime

router = APIRouter()

# SINGLE SOURCE OF TRUTH: backend/data
DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
PENDING_FILE = DATA_DIR / "pending.json"

def load_json(file_path):
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                if "pending" in data:
                    return data["pending"]
                if "users" in data:
                    return data["users"]
                return []
            return data
    except:
        return []

def save_json(file_path, data):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@router.post("/register")
async def register(payload: dict):
    society_id = payload.get("society_id", "sev2").strip() or "sev2"
    flat = payload.get("flat", "").strip()
    name = payload.get("name", "").strip()
    phone = payload.get("phone", "").strip()

    if not flat or not name or not phone:
        raise HTTPException(status_code=400, detail="Name, phone and flat are required")
    if len(phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    users = load_json(USERS_FILE)
    pending = load_json(PENDING_FILE)

    # Per-society phone uniqueness: same phone can register in different societies
    for u in users:
        if u.get("phone") == phone and u.get("society_id", "sev2") == society_id:
            raise HTTPException(status_code=400, detail=f"Phone is already registered in {society_id.upper()}.")
    for p in pending:
        if p.get("phone") == phone and p.get("society_id", "sev2") == society_id:
            raise HTTPException(status_code=400, detail=f"Phone is already registered in {society_id.upper()} (pending approval).")

    for u in users:
        if u.get("flat") == flat and u.get("society_id", "sev2") == society_id:
            raise HTTPException(status_code=400, detail=f"Flat {flat} is already registered.")
    for p in pending:
        if p.get("flat") == flat and p.get("society_id", "sev2") == society_id:
            raise HTTPException(status_code=400, detail=f"Flat {flat} is already pending approval.")

    new_entry = {
        "society_id": society_id,
        "flat": flat,
        "name": name,
        "phone": phone,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    pending.append(new_entry)
    save_json(PENDING_FILE, pending)
    return {"message": f"Registration request for {flat} submitted. Waiting for admin approval.", "flat": flat}

@router.get("/pending")
async def get_pending():
    pending = load_json(PENDING_FILE)
    return {"pending": pending, "count": len(pending)}

@router.get("/users")
async def get_users():
    users = load_json(USERS_FILE)
    return {"users": users, "count": len(users)}

@router.post("/approve")
async def approve(payload: dict):
    phone = payload.get("phone", "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone is required")
    pending = load_json(PENDING_FILE)
    users = load_json(USERS_FILE)
    found = None
    remaining = []
    for p in pending:
        if p.get("phone") == phone:
            found = p
        else:
            remaining.append(p)
    if not found:
        raise HTTPException(status_code=404, detail=f"No pending request found for phone {phone}")
    found["status"] = "approved"
    found["approved_at"] = datetime.now().isoformat()
    users.append(found)
    save_json(USERS_FILE, users)
    save_json(PENDING_FILE, remaining)
    return {"message": f"Approved {found.get('flat')} - {found.get('name')}", "user": found}

@router.post("/reject")
async def reject(payload: dict):
    phone = payload.get("phone", "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone is required")
    pending = load_json(PENDING_FILE)
    found = None
    remaining = []
    for p in pending:
        if p.get("phone") == phone:
            found = p
        else:
            remaining.append(p)
    if not found:
        raise HTTPException(status_code=404, detail=f"No pending request found for phone {phone}")
    save_json(PENDING_FILE, remaining)
    return {"message": f"Rejected {found.get('flat')} - {found.get('name')}", "rejected": found}

@router.post("/bulk-approve")
async def bulk_approve():
    pending = load_json(PENDING_FILE)
    users = load_json(USERS_FILE)
    if not pending:
        return {"message": "No pending requests", "approved_count": 0}
    for p in pending:
        p["status"] = "approved"
        p["approved_at"] = datetime.now().isoformat()
        users.append(p)
    count = len(pending)
    save_json(USERS_FILE, users)
    save_json(PENDING_FILE, [])
    return {"message": f"Approved all {count} pending users", "approved_count": count}

@router.post("/login")
async def login(payload: dict):
    phone = payload.get("phone","").strip()
    society_id = payload.get("society_id","").strip().lower()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone required")
    users = load_json(USERS_FILE)
    # Find user by phone, optionally filtered by society
    found = None
    for u in users:
        if u.get("phone") == phone:
            if not society_id or u.get("society_id","sev2").lower() == society_id:
                found = u
                break
    if not found:
        # Check pending
        pending = load_json(PENDING_FILE)
        for p in pending:
            if p.get("phone") == phone:
                if not society_id or p.get("society_id","sev2").lower() == society_id:
                    return {"status":"pending","message":f"Registration for {p.get('flat')} is pending admin approval","user":p}
        raise HTTPException(status_code=404, detail="Phone not registered. Please register your flat first.")
    return {"status":"approved","message":"Login successful","user":found}

@router.get("/stats")
async def stats():
    users = load_json(USERS_FILE)
    pending = load_json(PENDING_FILE)
    return {
        "total_users": len(users),
        "pending_count": len(pending),
        "data_dir": str(DATA_DIR),
        "users_file": str(USERS_FILE),
        "pending_file": str(PENDING_FILE)
    }
