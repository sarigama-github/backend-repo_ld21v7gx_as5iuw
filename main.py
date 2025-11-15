import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents

app = FastAPI(title="GMRC Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InitPayload(BaseModel):
    stations: Optional[List[dict]] = None
    fares: Optional[List[dict]] = None

class BookingPayload(BaseModel):
    user_name: str
    phone: str
    from_code: str
    to_code: str

@app.get("/")
def root():
    return {"service": "GMRC Booking API", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# ---------- GMRC domain logic ----------

# Utility: ensure base data exists (stations + fares)
@app.post("/api/init")
def init_data(payload: InitPayload):
    stations = payload.stations or []
    fares = payload.fares or []

    # Upsert stations
    for st in stations:
        db["station"].update_one({"code": st["code"]}, {"$set": st}, upsert=True)

    # Upsert fares
    for fr in fares:
        key = {"from_code": fr["from_code"], "to_code": fr["to_code"]}
        db["fare"].update_one(key, {"$set": fr}, upsert=True)

    return {"message": "Initialized", "stations": len(stations), "fares": len(fares)}

@app.get("/api/stations")
def list_stations():
    stations = list(db["station"].find({}, {"_id": 0}))
    return {"stations": stations}

@app.get("/api/fare")
def get_fare(from_code: str, to_code: str):
    fare = db["fare"].find_one({"from_code": from_code, "to_code": to_code}, {"_id": 0})
    if not fare:
        raise HTTPException(status_code=404, detail="Fare not found")
    return fare

@app.post("/api/book")
def create_booking(payload: BookingPayload):
    # look up fare
    fare_doc = db["fare"].find_one({"from_code": payload.from_code, "to_code": payload.to_code})
    if not fare_doc:
        raise HTTPException(status_code=404, detail="Fare not configured for this route")

    booking = {
        "user_name": payload.user_name,
        "phone": payload.phone,
        "from_code": payload.from_code,
        "to_code": payload.to_code,
        "fare": float(fare_doc.get("price", 0)),
        "status": "confirmed",
    }
    _id = create_document("booking", booking)
    return {"id": _id, **booking}

@app.get("/api/bookings")
def list_bookings(limit: int = 50):
    docs = get_documents("booking", {}, limit)
    # sanitize _id
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
    return {"bookings": docs}
