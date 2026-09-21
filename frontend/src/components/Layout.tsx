import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { api } from "../api/client";

const floorNav = [
  { to: "/calls", label: "呼", full: "呼梯", floorHint: "C" },
  { to: "/dispatch", label: "派", full: "派工", floorHint: "D" },
  { to: "/cars", label: "厢", full: "轿厢", floorHint: "A" },
  { to: "/buildings", label: "栋", full: "楼栋", floorHint: "B" },
  { to: "/replay", label: "回", full: "回放", floorHint: "R" },
  { to: "/congestion", label: "堵", full: "拥堵", floorHint: "G" },
];

type Car = { id: number; label: string; floor: number; direction: string; load: number; capacity: number };
type Call = { id: number; floor: number; status: string };
type B = { floors: number; name?: string };

export default function Layout() {
  const [cars, setCars] = useState<Car[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [floors, setFloors] = useState(12);
  const [bName, setBName] = useState("LiftBay");

  useEffect(() => {
    const load = () => {
      api<Car[]>("/cars").then(setCars).catch(() => {});
      api<Call[]>("/calls").then(setCalls).catch(() => {});
      api<B[]>("/buildings").then((bs) => {
        if (bs[0]) {
          setFloors(bs[0].floors);
          if (bs[0].name) setBName(bs[0].name);
        }
      }).catch(() => {});
    };
    load();
    const t = setInterval(load, 6000);
    return () => clearInterval(t);
  }, []);

  const callFloors = useMemo(
    () => new Set(calls.filter((c) => c.status === "waiting").map((c) => c.floor)),
    [calls]
  );
  const levels = useMemo(() => Array.from({ length: floors }, (_, i) => floors - i), [floors]);
  const waiting = calls.filter((c) => c.status === "waiting").length;

  return (
    <div className="shaft-shell">
      <aside className="elevation-column" aria-label="井道立面">
        <div className="elevation-header">
          <div className="elevation-title">{bName}</div>
          <div className="elevation-sub">井道立面 · {floors}F</div>
        </div>

        <div className="shaft-edge-nav">
          {floorNav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              title={n.full}
              className={({ isActive }) =>
                `floor-pill${isActive ? " floor-pill--active" : ""}`
              }
            >
              <span className="floor-pill-hint">{n.floorHint}</span>
              <span className="floor-pill-label">{n.label}</span>
            </NavLink>
          ))}
        </div>

        <div className="shaft-bank">
          {cars.length === 0 && (
            <div className="shaft-empty-col">
              {levels.map((f) => (
                <div key={f} className="elev-floor">
                  <span className="elev-floor-num">{f}</span>
                </div>
              ))}
            </div>
          )}
          {cars.map((car) => (
            <div className="elev-shaft" key={car.id}>
              <div className="elev-shaft-cap">
                {car.label}
                <span className="mono">
                  {car.load}/{car.capacity}
                </span>
              </div>
              <div className="elev-shaft-well">
                {levels.map((f) => {
                  const here = car.floor === f;
                  const call = callFloors.has(f);
                  return (
                    <div
                      key={f}
                      className={`elev-floor${here ? " elev-floor--car" : ""}${call ? " elev-floor--call" : ""}`}
                    >
                      <span className="elev-floor-num">{f}</span>
                      {here && (
                        <span className="elev-car-glyph" title={car.direction}>
                          {car.direction === "down" ? "▼" : car.direction === "up" ? "▲" : "●"}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <div className="elevation-footer">
          待派呼梯 <strong>{waiting}</strong>
        </div>
      </aside>

      <section className="dispatch-deck">
        <header className="dispatch-deck-bar">
          <h1 className="dispatch-deck-brand">LiftBay 派梯台</h1>
          <span className="dispatch-deck-hint">左侧井道 · 右侧队列</span>
        </header>
        <div className="dispatch-deck-body">
          <Outlet />
        </div>
      </section>
    </div>
  );
}
