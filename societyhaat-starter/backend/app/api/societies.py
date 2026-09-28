
from fastapi import APIRouter
router = APIRouter()

# PLUG & PLAY - Add new society here, no code change needed elsewhere - lives in 60s
SOCIETIES = [
    {
        "id": "sev2",
        "code": "SEV2",
        "full_name": "Supertech Eco Village 2",
        "display": "Supertech Eco Village 2 (SEV2)",
        "address": "Greater Noida West - 201306",
        "color": "#16a34a",
        "radius_km": 1.2,
        "listings": 142,
        "active": True
    },
    {
        "id": "apcpth",
        "code": "APCPTH",
        "full_name": "Amrapali Centurion Park Terrace Homes",
        "display": "Amrapali Centurion Park Terrace Homes (APCPTH)",
        "address": "Greater Noida West - 201308 - Terrace Homes",
        "color": "#2563eb",
        "radius_km": 1.2,
        "listings": 89,
        "active": True
    },
    {
        "id": "alp",
        "code": "ALP",
        "full_name": "Amrapali Leisure Park",
        "display": "Amrapali Leisure Park (ALP)",
        "color": "#ea580c",
        "radius_km": 1.2,
        "listings": 67,
        "active": True
    }
]

@router.get("")
def list_societies():
    return {"total": len(SOCIETIES), "cluster": "1-2km Greater Noida West", "societies": SOCIETIES}

@router.post("")
def add_society(society: dict):
    # Plug & Play: Admin adds via API, no deploy needed - cached 60s
    SOCIETIES.append(society)
    return {"message": "Society added - Live in 60s", "society": society, "plug_and_play": True}

@router.get("/{society_id}")
def get_society(society_id: str):
    for s in SOCIETIES:
        if s["id"] == society_id:
            return s
    return {"error": "Not found"}
