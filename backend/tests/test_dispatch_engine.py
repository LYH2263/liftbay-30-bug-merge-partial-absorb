from app.services.dispatch_engine import (
    CallRequest,
    CarState,
    can_merge_group,
    pick_car,
    score_car,
)


def test_reject_when_full():
    car = CarState(1, 5, "idle", load=8, capacity=8)
    call = CallRequest(1, 5, "up", passengers=1)
    r = score_car(car, call)
    assert r.accepted is False
    assert "满员" in r.reason


def test_same_direction_beats_far_idle():
    cars = [
        CarState(1, 2, "up", load=1, capacity=10),
        CarState(2, 12, "idle", load=0, capacity=10),
    ]
    call = CallRequest(9, 4, "up", 1)
    best = pick_car(cars, call)
    assert best is not None
    assert best.car_id == 1


def test_closer_idle_wins_when_opposite():
    cars = [
        CarState(1, 10, "down", load=0, capacity=10),
        CarState(2, 3, "idle", load=0, capacity=10),
    ]
    call = CallRequest(3, 2, "up", 1)
    best = pick_car(cars, call)
    assert best is not None
    assert best.car_id == 2


def test_can_merge_group_capacity_check():
    tight = CarState(1, 1, "idle", load=4, capacity=8)  # 剩余 4
    roomy = CarState(2, 1, "idle", load=0, capacity=10)  # 剩余 10
    assert can_merge_group([tight], 4) is True  # 恰好接得住
    assert can_merge_group([tight], 5) is False  # 唯一轿厢接不住
    assert can_merge_group([tight, roomy], 5) is True  # 任一台够即可
    assert can_merge_group([], 1) is False  # 无轿厢
