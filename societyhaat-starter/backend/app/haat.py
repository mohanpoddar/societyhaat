from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from datetime import datetime
import uuid

router = APIRouter()
DATA_DIR = Path(__file__).parent.parent / "data"
HAAT_FILE = DATA_DIR / "haat.json"

def load_haat():
    if not HAAT_FILE.exists():
        return []
    try:
        with open(HAAT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get('posts', [])
    except:
        return []

def save_haat(data):
    HAAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HAAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@router.get("/list")
async def list_haat(society_id: str = "", category: str = ""):
    posts = load_haat()
    # Filter by society isolation
    if society_id:
        posts = [p for p in posts if p.get('society_id','sev2').lower() == society_id.lower()]
    if category:
        posts = [p for p in posts if p.get('category','').lower() == category.lower()]
    # newest first
    posts = sorted(posts, key=lambda x: x.get('created_at',''), reverse=True)
    return {"posts": posts, "count": len(posts)}

@router.post("/create")
async def create_haat(payload: dict):
    society_id = payload.get("society_id","sev2").strip() or "sev2"
    title = payload.get("title","").strip()
    description = payload.get("description","").strip()
    price = payload.get("price","")
    category = payload.get("category","Home Food").strip()
    phone = payload.get("phone","").strip()
    name = payload.get("name","Anonymous").strip()
    flat = payload.get("flat","").strip()

    if not title or not description:
        raise HTTPException(status_code=400, detail="Title and description required")
    
    posts = load_haat()
    new_post = {
        "id": str(uuid.uuid4())[:8],
        "society_id": society_id,
        "title": title,
        "description": description,
        "price": price,
        "category": category,
        "phone": phone,
        "name": name,
        "flat": flat,
        "photos": payload.get("photos", []),  # list of webp names
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    posts.append(new_post)
    save_haat(posts)
    return {"message": f"Posted to {society_id.upper()} Haat", "post": new_post}

@router.post("/delete")
async def delete_haat(payload: dict):
    post_id = payload.get("id","").strip()
    if not post_id:
        raise HTTPException(status_code=400, detail="id required")
    posts = load_haat()
    remaining = [p for p in posts if p.get('id') != post_id]
    if len(remaining) == len(posts):
        raise HTTPException(status_code=404, detail="Post not found")
    save_haat(remaining)
    return {"message": "Deleted"}
