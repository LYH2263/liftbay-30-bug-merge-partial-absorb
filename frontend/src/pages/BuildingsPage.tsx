import { useEffect, useState } from "react";
import { api } from "../api/client";
type B = { id: number; name: string; floors: number };
export default function BuildingsPage() {
  const [rows, setRows] = useState<B[]>([]);
  useEffect(() => { api<B[]>("/buildings").then(setRows); }, []);
  return (<>
    <h2>楼栋</h2>
    <table className="table"><thead><tr><th>名称</th><th>楼层数</th></tr></thead>
    <tbody>{rows.map(b => <tr key={b.id}><td>{b.name}</td><td className="mono">{b.floors}</td></tr>)}</tbody></table>
  </>);
}
