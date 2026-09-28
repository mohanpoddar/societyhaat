
from fastapi import APIRouter
router = APIRouter()

# Demo listings for Haat + Seva
LISTINGS = [
    {"id": "1", "society_id": "sev2", "tab": "Haat", "category": "Home Food", "title": "Homemade Chocolate Cake - 3 photos", "images": ["cake1.webp","cake2.webp","cake3.webp"], "price": 450, "verified": "SEV2 Tower 4 - 1202", "user": "Sunita Aunty"},
    {"id": "2", "society_id": "sev2", "tab": "Seva", "category": "Car Pooling", "title": "Pari Chowk 8:30 AM - 2 seats - SEV2 to APCPTH", "images": ["car1.webp"], "price": 0, "verified": "SEV2", "user": "Rohit"},
    {"id": "3", "society_id": "apcpth", "tab": "Seva", "category": "Help Old-Age", "title": "Need help for morning walk - Uncle in Tower 2", "images": [], "price": 0, "verified": "APCPTH", "user": "Anil"},
]

@router.get("")
def get_listings(society_id: str = None, tab: str = None):
    filtered = LISTINGS
    if society_id:
        filtered = [l for l in filtered if l["society_id"] == society_id]
    if tab:
        filtered = [l for l in filtered if l["tab"] == tab]
    return {"count": len(filtered), "listings": filtered, "isolated": True if society_id else False}

@router.post("")
def create_listing(listing: dict):
    LISTINGS.append(listing)
    return {"message": "Posted", "listing": listing}
