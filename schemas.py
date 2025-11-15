"""
Database Schemas for GMRC Booking App

Each Pydantic model represents a MongoDB collection. The collection name
is the lowercase of the class name (e.g., Booking -> "booking").
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal

class Station(BaseModel):
    code: str = Field(..., description="Unique short code for the station, e.g., OHC")
    name: str = Field(..., description="Station display name")
    line: Literal["Red", "Blue"] = Field(..., description="Metro line")
    order: int = Field(..., ge=0, description="Order along the line to compute hops")

class Fare(BaseModel):
    from_code: str = Field(..., description="Source station code")
    to_code: str = Field(..., description="Destination station code")
    price: float = Field(..., ge=0, description="Fare amount in INR")

class Booking(BaseModel):
    user_name: str = Field(..., description="Passenger full name")
    phone: str = Field(..., description="Contact phone number")
    from_code: str = Field(..., description="Source station code")
    to_code: str = Field(..., description="Destination station code")
    fare: float = Field(..., ge=0, description="Fare charged in INR")
    status: Literal["confirmed", "cancelled"] = Field("confirmed", description="Booking status")
