import { useEffect, useState } from "react";
import { api } from "../api/client";
type C = { floor: number; passengers: number };
export default function CongestionPage() {
  const [rows, setRows] = useState<C[]>([]);
  useEffect(() => { api<C[]>("/congestion").then(setRows); }, []);
  const max = Math.max(1, ...rows.map(r => r.passengers));
  return (<>
    <h2>拥堵</h2>
    <table className="table"><thead><tr><th>楼层</th><th>等待人数</th><th></th></tr></thead>
    <tbody>{rows.map(r => <tr key={r.floor}><td className="mono">{r.floor}F</td><td>{r.passengers}</td>
      <td><div className="congestion-bar" style={{ width: `${(r.passengers / max) * 240}px` }} /></td></tr>)}
      {!rows.length && <tr><td colSpan={3}>当前无等待拥堵</td></tr>}
    </tbody></table>
  </>);
}
