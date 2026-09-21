from app.models.models import Building, CallTicket, ElevatorCar


def _world(db, *, car_capacity: int, car_load: int):
    """一栋楼 + 一台轿厢 + 两笔同层同向上行 waiting 呼梯（2 人和 3 人）。"""
    b = Building(name="测试楼", floors=10)
    db.add(b)
    db.flush()
    car = ElevatorCar(
        building_id=b.id, label="T1", floor=1, direction="idle",
        load=car_load, capacity=car_capacity,
    )
    db.add(car)
    db.flush()
    c1 = CallTicket(building_id=b.id, floor=3, direction="up", passengers=2, status="waiting")
    c2 = CallTicket(building_id=b.id, floor=3, direction="up", passengers=3, status="waiting")
    db.add_all([c1, c2])
    db.commit()
    return b, car, c1, c2


def test_merge_fails_when_no_car_has_capacity_and_keeps_originals(client, db):
    # 剩余容量 8-4=4 < 2+3，合并必须失败
    _, car, c1, c2 = _world(db, car_capacity=8, car_load=4)

    resp = client.post("/api/calls/merge", json={"call_ids": [c1.id, c2.id]})
    assert resp.status_code == 409

    calls = client.get("/api/calls").json()
    mine = {c["id"]: c for c in calls if c["id"] in (c1.id, c2.id)}
    assert len(mine) == 2  # 原多笔保持不变
    assert mine[c1.id]["status"] == "waiting"
    assert mine[c2.id]["status"] == "waiting"
    assert mine[c1.id]["passengers"] == 2
    assert mine[c2.id]["passengers"] == 3
    db.expire_all()
    assert db.get(ElevatorCar, car.id).load == 4  # 轿厢载荷未动


def test_merge_success_leaves_single_waiting_call(client, db):
    # 剩余容量 10 >= 2+3，合并成功
    _, _, c1, c2 = _world(db, car_capacity=10, car_load=0)

    resp = client.post("/api/calls/merge", json={"call_ids": [c1.id, c2.id]})
    assert resp.status_code == 200
    merged = resp.json()
    assert merged["id"] == c1.id  # 保留首笔
    assert merged["passengers"] == 5
    assert merged["status"] == "waiting"

    calls = client.get("/api/calls").json()
    waiting = [c for c in calls if c["status"] == "waiting"]
    assert len(waiting) == 1  # 只剩一笔 waiting
    assert waiting[0]["id"] == c1.id
    assert waiting[0]["passengers"] == 5
    assert all(c["id"] != c2.id for c in calls)  # 被合并的一笔已消失


def test_merged_call_congestion_and_dispatch_load_match(client, db):
    _, car, c1, c2 = _world(db, car_capacity=10, car_load=0)
    merged = client.post("/api/calls/merge", json={"call_ids": [c1.id, c2.id]}).json()

    congestion = client.get("/api/congestion").json()
    assert congestion == [{"floor": 3, "passengers": 5}]  # 拥堵按合并后人数计

    resp = client.post("/api/dispatch", json={"call_id": merged["id"]})
    assert resp.status_code == 200
    assert resp.json()["assigned_car_id"] == car.id

    cars = client.get("/api/cars").json()
    t1 = next(c for c in cars if c["id"] == car.id)
    assert t1["load"] == 5  # 轿厢载荷一次加上总人数，与拥堵人数对上
    assert client.get("/api/congestion").json() == []  # 派工后不再拥堵


def test_merge_rejects_cross_floor_or_direction(client, db):
    b = Building(name="测试楼", floors=10)
    db.add(b)
    db.flush()
    db.add(ElevatorCar(building_id=b.id, label="T1", floor=1, direction="idle", load=0, capacity=10))
    c1 = CallTicket(building_id=b.id, floor=3, direction="up", passengers=2, status="waiting")
    c2 = CallTicket(building_id=b.id, floor=4, direction="up", passengers=3, status="waiting")
    c3 = CallTicket(building_id=b.id, floor=3, direction="down", passengers=1, status="waiting")
    db.add_all([c1, c2, c3])
    db.commit()

    assert client.post("/api/calls/merge", json={"call_ids": [c1.id, c2.id]}).status_code == 400
    assert client.post("/api/calls/merge", json={"call_ids": [c1.id, c3.id]}).status_code == 400
    assert len(client.get("/api/calls").json()) == 3  # 均未变动


def test_merge_rejects_non_waiting_and_unknown_ids(client, db):
    _, _, c1, c2 = _world(db, car_capacity=10, car_load=0)
    c2.status = "assigned"
    db.commit()

    assert client.post("/api/calls/merge", json={"call_ids": [c1.id, c2.id]}).status_code == 400
    assert client.post("/api/calls/merge", json={"call_ids": [c1.id, 9999]}).status_code == 404
    assert client.post("/api/calls/merge", json={"call_ids": [c1.id, c1.id]}).status_code == 400
