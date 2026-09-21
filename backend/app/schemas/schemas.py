from datetime import datetime
from pydantic import BaseModel, Field


class BuildingOut(BaseModel):
    id: int
    name: str
    floors: int
    model_config = {"from_attributes": True}


class CarOut(BaseModel):
    id: int
    building_id: int
    label: str
    floor: int
    direction: str
    load: int
    capacity: int
    model_config = {"from_attributes": True}


class CallOut(BaseModel):
    id: int
    building_id: int
    floor: int
    direction: str
    passengers: int
    status: str
    assigned_car_id: int | None
    score: str
    created_at: datetime
    model_config = {"from_attributes": True}


class CallCreate(BaseModel):
    building_id: int
    floor: int = Field(ge=1)
    direction: str
    passengers: int = Field(ge=1, le=8)


class DispatchRequest(BaseModel):
    call_id: int


class MergeRequest(BaseModel):
    call_ids: list[int] = Field(min_length=2)


class LogOut(BaseModel):
    id: int
    call_id: int
    car_id: int | None
    detail: str
    created_at: datetime
    model_config = {"from_attributes": True}


class CongestionFloor(BaseModel):
    floor: int
    passengers: int
