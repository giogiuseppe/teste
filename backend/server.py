from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time
import os
import uuid
from bson import ObjectId

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
db = client.bar_booking
tables_collection = db.tables
bookings_collection = db.bookings

# Pydantic models
class Table(BaseModel):
    id: str
    name: str
    capacity: int
    location: Optional[str] = None

class BookingRequest(BaseModel):
    table_id: str
    customer_name: str
    customer_phone: str
    party_size: int
    booking_date: str  # YYYY-MM-DD format
    booking_time: str  # HH:MM format
    special_requests: Optional[str] = None

class Booking(BaseModel):
    id: str
    table_id: str
    table_name: str
    customer_name: str
    customer_phone: str
    party_size: int
    booking_date: str
    booking_time: str
    special_requests: Optional[str] = None
    created_at: datetime

class AvailabilityRequest(BaseModel):
    booking_date: str
    booking_time: str
    party_size: int

# Initialize tables on startup
def initialize_tables():
    if tables_collection.count_documents({}) == 0:
        initial_tables = [
            {"id": str(uuid.uuid4()), "name": "Table 1", "capacity": 2, "location": "Window"},
            {"id": str(uuid.uuid4()), "name": "Table 2", "capacity": 4, "location": "Center"},
            {"id": str(uuid.uuid4()), "name": "Table 3", "capacity": 4, "location": "Center"},
            {"id": str(uuid.uuid4()), "name": "Table 4", "capacity": 6, "location": "Corner"},
            {"id": str(uuid.uuid4()), "name": "Table 5", "capacity": 2, "location": "Bar"},
            {"id": str(uuid.uuid4()), "name": "Table 6", "capacity": 8, "location": "Private"},
            {"id": str(uuid.uuid4()), "name": "Table 7", "capacity": 4, "location": "Center"},
            {"id": str(uuid.uuid4()), "name": "Table 8", "capacity": 2, "location": "Window"},
            {"id": str(uuid.uuid4()), "name": "Table 9", "capacity": 6, "location": "Corner"},
            {"id": str(uuid.uuid4()), "name": "Table 10", "capacity": 4, "location": "Center"},
            {"id": str(uuid.uuid4()), "name": "Bar Counter 1", "capacity": 8, "location": "Bar"},
            {"id": str(uuid.uuid4()), "name": "Bar Counter 2", "capacity": 6, "location": "Bar"},
        ]
        tables_collection.insert_many(initial_tables)

# Initialize tables on startup
initialize_tables()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Bar booking API is running"}

@app.get("/api/tables")
async def get_tables():
    try:
        tables = list(tables_collection.find({}, {"_id": 0}))
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-availability")
async def check_availability(request: AvailabilityRequest):
    try:
        # Find all tables that can accommodate the party size
        suitable_tables = list(tables_collection.find(
            {"capacity": {"$gte": request.party_size}}, 
            {"_id": 0}
        ))
        
        # Check which tables are already booked for this date/time
        booked_tables = list(bookings_collection.find({
            "booking_date": request.booking_date,
            "booking_time": request.booking_time
        }, {"table_id": 1, "_id": 0}))
        
        booked_table_ids = [booking["table_id"] for booking in booked_tables]
        
        # Filter out booked tables
        available_tables = [
            table for table in suitable_tables 
            if table["id"] not in booked_table_ids
        ]
        
        return {
            "available_tables": available_tables,
            "booking_date": request.booking_date,
            "booking_time": request.booking_time,
            "party_size": request.party_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bookings")
async def create_booking(booking: BookingRequest):
    try:
        # Check if table exists
        table = tables_collection.find_one({"id": booking.table_id}, {"_id": 0})
        if not table:
            raise HTTPException(status_code=404, detail="Table not found")
        
        # Check if table is available
        existing_booking = bookings_collection.find_one({
            "table_id": booking.table_id,
            "booking_date": booking.booking_date,
            "booking_time": booking.booking_time
        })
        
        if existing_booking:
            raise HTTPException(status_code=400, detail="Table is already booked for this time")
        
        # Check if party size fits table capacity
        if booking.party_size > table["capacity"]:
            raise HTTPException(status_code=400, detail="Party size exceeds table capacity")
        
        # Create new booking
        new_booking = {
            "id": str(uuid.uuid4()),
            "table_id": booking.table_id,
            "table_name": table["name"],
            "customer_name": booking.customer_name,
            "customer_phone": booking.customer_phone,
            "party_size": booking.party_size,
            "booking_date": booking.booking_date,
            "booking_time": booking.booking_time,
            "special_requests": booking.special_requests,
            "created_at": datetime.now()
        }
        
        bookings_collection.insert_one(new_booking)
        
        # Return booking confirmation (remove _id for JSON serialization)
        new_booking.pop('_id', None)
        return new_booking
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bookings")
async def get_bookings(date: Optional[str] = None):
    try:
        query = {}
        if date:
            query["booking_date"] = date
            
        bookings = list(bookings_collection.find(query, {"_id": 0}))
        return bookings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bookings/{booking_id}")
async def get_booking(booking_id: str):
    try:
        booking = bookings_collection.find_one({"id": booking_id}, {"_id": 0})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)