
# Society Haat - Production Starter - Haat + Seva

Cluster: Greater Noida West 1-2km
Societies:
- Supertech Eco Village 2 (SEV2) - 142 listings
- Amrapali Centurion Park Terrace Homes (APCPTH) - NOT APCT - 89 listings
- Amrapali Leisure Park (ALP) - 67 listings

Brand: Society Haat - Haat + Seva (touchy, covers bazaar + old-age help + car pooling)

## Backend (Python FastAPI on Google Cloud)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Test: http://localhost:8000/api/societies - shows full names

Deploy to Cloud Run:
gcloud builds submit --config cloudbuild.yaml

Plug & Play: POST /api/societies to add new society - live in 60s, no code deploy

Photo upload: POST /api/uploads/image - max 5 photos, 5MB each, first is cover - for cakes 3 photos

## Frontend Flutter
cd app_flutter
flutter pub get
flutter run

Build APK to share in society WhatsApp:
flutter build apk --release

## VS Code Integration
You have Meta AI on right via Simple Browser: https://www.meta.ai
Ask: "Add new category" -> I give code -> paste left

Easy to update: edit file, git push, cloud build deploys backend, shorebird patch for app.
