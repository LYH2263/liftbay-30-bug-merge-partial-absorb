from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Building, CallTicket, DispatchLog, ElevatorCar
from app.schemas.schemas import (
    BuildingOut,
    CallCreate,
    CallOut,
    CarOut,
    CongestionFloor,
    DispatchRequest,
    LogOut,
    MergeRequest,
)
from app.services.dispatch_engine import (
    CallRequest,
    CarState,
    can_merge_group,
    congestion_by_floor,
    pick_car,
)

api_router = APIRouter()


@api_router.get("/health")
def health():
    return {"status": "ok"}


@api_router.get("/buildings", response_model=list[BuildingOut])
def buildings(db: Session = Depends(get_db)):
    return db.scalars(select(Building).order_by(Building.id)).all()


@api_router.get("/cars", response_model=list[CarOut])
def cars(db: Session = Depends(get_db)):
    return db.scalars(select(ElevatorCar).order_by(ElevatorCar.id)).all()


@api_router.get("/calls", response_model=list[CallOut])
def calls(db: Session = Depends(get_db)):
    return db.scalars(select(CallTicket).order_by(CallTicket.id.desc())).all()


@api_router.post("/calls", response_model=CallOut)
def create_call(body: CallCreate, db: Session = Depends(get_db)):
    b = db.get(Building, body.building_id)
    if not b:
        raise HTTPException(404, "楼栋不存在")
    if body.floor > b.floors:
        raise HTTPException(400, "楼层超出")
    if body.direction not in ("up", "down"):
        raise HTTPException(400, "方向无效")
    ticket = CallTicket(
        building_id=body.building_id,
        floor=body.floor,
        direction=body.direction,
        passengers=body.passengers,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@api_router.post("/calls/merge", response_model=CallOut)
def merge_calls(body: MergeRequest, db: Session = Depends(get_db)):
    ids = sorted(set(body.call_ids))
    if len(ids) < 2:
        raise HTTPException(400, "至少选择两笔不同的呼梯")
    tickets = db.scalars(
        select(CallTicket).where(CallTicket.id.in_(ids)).order_by(CallTicket.id)
    ).all()
    if len(tickets) != len(ids):
        raise HTTPException(404, "呼梯不存在")
    if any(t.status != "waiting" for t in tickets):
        raise HTTPException(400, "仅等待中的呼梯可合并")
    first = tickets[0]
    if any(
        t.building_id != first.building_id
        or t.floor != first.floor
        or t.direction != first.direction
        for t in tickets
    ):
        raise HTTPException(400, "仅同楼栋同层同向的呼梯可合并")
    total = sum(t.passengers for t in tickets)
    car_rows = db.scalars(
        select(ElevatorCar).where(ElevatorCar.building_id == first.building_id)
    ).all()
    cars = [CarState(c.id, c.floor, c.direction, c.load, c.capacity) for c in car_rows]
    if not can_merge_group(cars, total):
        raise HTTPException(409, "合并后总人数超出所有轿厢剩余容量")
    first.passengers = total
    for t in tickets[1:]:
        db.delete(t)
    db.add(
        DispatchLog(
            call_id=first.id,
            car_id=None,
            detail=f"同层同向合并 {len(tickets)} 笔为 #{first.id}，共 {total} 人",
        )
    )
    db.commit()
    db.refresh(first)
    return first


@api_router.post("/dispatch", response_model=CallOut)
def dispatch(body: DispatchRequest, db: Session = Depends(get_db)):
    ticket = db.get(CallTicket, body.call_id)
    if not ticket:
        raise HTTPException(404, "呼梯不存在")
    if ticket.status != "waiting":
        raise HTTPException(400, "呼梯已处理")
    car_rows = db.scalars(
        select(ElevatorCar).where(ElevatorCar.building_id == ticket.building_id)
    ).all()
    cars = [
        CarState(c.id, c.floor, c.direction, c.load, c.capacity) for c in car_rows
    ]
    call = CallRequest(ticket.id, ticket.floor, ticket.direction, ticket.passengers)
    best = pick_car(cars, call)
    if best is None:
        db.add(DispatchLog(call_id=ticket.id, car_id=None, detail="全部轿厢满员，拒绝派工"))
        ticket.status = "rejected"
        db.commit()
        db.refresh(ticket)
        raise HTTPException(409, "无可用轿厢（满员）")
    car = db.get(ElevatorCar, best.car_id)
    assert car
    ticket.status = "assigned"
    ticket.assigned_car_id = car.id
    ticket.score = f"{best.score:.1f}"
    car.load += ticket.passengers
    car.floor = ticket.floor
    car.direction = ticket.direction
    db.add(
        DispatchLog(
            call_id=ticket.id,
            car_id=car.id,
            detail=f"派予 {car.label}，评分 {best.score:.1f}（同向/距离综合）",
        )
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@api_router.get("/replay", response_model=list[LogOut])
def replay(db: Session = Depends(get_db)):
    return db.scalars(select(DispatchLog).order_by(DispatchLog.id.desc())).all()


@api_router.get("/congestion", response_model=list[CongestionFloor])
def congestion(db: Session = Depends(get_db)):
    waiting = db.scalars(select(CallTicket).where(CallTicket.status == "waiting")).all()
    counts = congestion_by_floor(
        [CallRequest(c.id, c.floor, c.direction, c.passengers) for c in waiting]
    )
    return [
        CongestionFloor(floor=f, passengers=p)
        for f, p in sorted(counts.items(), key=lambda x: -x[1])
    ]
