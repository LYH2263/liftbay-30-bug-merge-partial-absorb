import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
type Car = { id: number; label: string; floor: number; direction: string; load: number; capacity: number };
type Call = { id: number; floor: number; status: string };
type B = { floors: number };
export default function CarsPage() {
  const [cars, setCars] = useState<Car[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [floors, setFloors] = useState(18);
  useEffect(() => {
    api<Car[]>("/cars").then(setCars);
    api<Call[]>("/calls").then(setCalls);
    api<B[]>("/buildings").then(bs => { if (bs[0]) setFloors(bs[0].floors); });
  }, []);
  const callFloors = useMemo(() => new Set(calls.filter(c => c.status === "waiting").map(c => c.floor)), [calls]);
  const levels = useMemo(() => Array.from({ length: floors }, (_, i) => i + 1), [floors]);
  return (<>
    <h2>轿厢井道</h2>
    <div className="shaft-wrap">
      {cars.map(car => (
        <div className="shaft" key={car.id}>
          <h3>{car.label} · {car.load}/{car.capacity}</h3>
          {levels.map(f => (
            <div key={f} className={`floor-slot ${car.floor === f ? "has-car" : ""} ${callFloors.has(f) ? "has-call" : ""}`}>
              {car.floor === f ? car.direction : f}
            </div>
          ))}
        </div>
      ))}
    </div>
  </>);
}
