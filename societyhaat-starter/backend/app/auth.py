from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from datetime import datetime

router = APIRouter()
DATA_DIR = Path(__file__).parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
PENDING_FILE = DATA_DIR / "pending.json"

SEED_USERS = [
    {"society_id":"sev2","flat":"B16-806","name":"Mohan Poddar","phone":"9560779666","status":"approved","created_at":datetime.now().isoformat(),"approved_at":datetime.now().isoformat(),"cars":[{"id":"Maruti_WagonR_9560779666","make":"Maruti Suzuki","model":"WagonR","type":"Hatchback","seats":"5 Seater","color":"White","number":"8060","ac":True,"created_at":datetime.now().isoformat()}]},
    {"society_id":"sev2","flat":"A2-102","name":"Piyush Poddar","phone":"9625561517","status":"approved","created_at":datetime.now().isoformat(),"approved_at":datetime.now().isoformat(),"cars":[]},
    {"society_id":"sev2","flat":"B16-805","name":"Test User","phone":"9999999999","status":"approved","created_at":datetime.now().isoformat(),"approved_at":datetime.now().isoformat(),"cars":[]}
]

def load_json(file_path):
    # Auto-seed if file missing or empty
    if not file_path.exists():
        if file_path.name == "users.json":
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(SEED_USERS, f, indent=2, ensure_ascii=False)
                print(f"✅ Auto-seeded {file_path}")
                return SEED_USERS.copy()
            except Exception as e:
                print(f"Seed failed: {e}")
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
            if not data and file_path.name == "users.json":
                # empty file -> seed
                with open(file_path, 'w', encoding='utf-8') as fw:
                    json.dump(SEED_USERS, fw, indent=2, ensure_ascii=False)
                return SEED_USERS.copy()
            return data
    except Exception as e:
        print(f"load_json error {file_path}: {e}")
        if file_path.name == "users.json":
            return SEED_USERS.copy()
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
    print(f"LOGIN attempt phone={phone} soc={society_id} users_count={len(users)} file={USERS_FILE}")
    found = None
    for u in users:
        if u.get("phone") == phone:
            if not society_id or u.get("society_id","sev2").lower() == society_id:
                found = u
                break
    if not found:
        for u in users:
            if u.get("phone") == phone:
                found = u
                break
    if not found:
        pending = load_json(PENDING_FILE)
        for p in pending:
            if p.get("phone") == phone:
                if not society_id or p.get("society_id","sev2").lower() == society_id:
                    return {"status":"pending","message":f"Registration for {p.get('flat')} is pending admin approval","user":p}
        for p in pending:
            if p.get("phone") == phone:
                return {"status":"pending","message":f"Registration for {p.get('flat')} is pending approval","user":p}
        print(f"LOGIN FAILED phone={phone} not in users count={len(users)}")
        raise HTTPException(status_code=404, detail=f"Phone {phone} not registered. Available: {', '.join([u.get('phone','') for u in users[:5]])} | Please register first")
    return {"status":"approved","message":"Login successful","user":found}

@router.post("/add-car")
async def add_car(payload: dict):
    phone = payload.get("phone","").strip()
    society_id = payload.get("society_id","").strip().lower() or "sev2"
    if not phone:
        raise HTTPException(status_code=400, detail="Phone required")
    car_make = payload.get("make","").strip()
    car_model = payload.get("model","").strip()
    car_type = payload.get("type","Hatchback").strip()
    seats = payload.get("seats","5").strip()
    color = payload.get("color","").strip()
    number = payload.get("number","").strip()
    ac = payload.get("ac", True)
    if not car_make or not car_model:
        raise HTTPException(status_code=400, detail="Car make and model required")
    users = load_json(USERS_FILE)
    found_idx = -1
    for i, u in enumerate(users):
        if u.get("phone") == phone and u.get("society_id","sev2").lower() == society_id:
            found_idx = i
            break
    if found_idx == -1:
        # try without society
        for i, u in enumerate(users):
            if u.get("phone") == phone:
                found_idx = i
                break
    if found_idx == -1:
        raise HTTPException(status_code=404, detail="User not found. Please register first.")
    car = {
        "id": f"{car_make}_{car_model}_{users[found_idx].get('phone','')}"[:30],
        "make": car_make,
        "model": car_model,
        "type": car_type,
        "seats": seats,
        "color": color,
        "number": number,
        "ac": ac,
        "created_at": datetime.now().isoformat()
    }
    if "cars" not in users[found_idx]:
        users[found_idx]["cars"] = []
    existing = -1
    for idx, c in enumerate(users[found_idx]["cars"]):
        if c.get("make")==car_make and c.get("model")==car_model:
            existing = idx
            break
    if existing >=0:
        users[found_idx]["cars"][existing] = car
    else:
        users[found_idx]["cars"].append(car)
    save_json(USERS_FILE, users)
    return {"message": f"Car {car_make} {car_model} saved", "car": car, "cars": users[found_idx]["cars"]}

@router.get("/cars")
async def get_cars(phone: str = "", society_id: str = "sev2"):
    if not phone:
        raise HTTPException(status_code=400, detail="Phone required")
    users = load_json(USERS_FILE)
    for u in users:
        if u.get("phone")==phone and u.get("society_id","sev2").lower()==society_id.lower():
            return {"cars": u.get("cars", []), "count": len(u.get("cars", []))}
    for u in users:
        if u.get("phone")==phone:
            return {"cars": u.get("cars", []), "count": len(u.get("cars", []))}
    pending = load_json(PENDING_FILE)
    for p in pending:
        if p.get("phone")==phone:
            return {"cars": p.get("cars", []), "count": len(p.get("cars", []))}
    raise HTTPException(status_code=404, detail="User not found")

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