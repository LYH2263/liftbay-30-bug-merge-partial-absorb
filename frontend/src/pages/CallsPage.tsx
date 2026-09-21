import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
type B = { id: number; name: string; floors: number };
type Call = { id: number; building_id: number; floor: number; direction: string; passengers: number; status: string; assigned_car_id: number | null; score: string };
export default function CallsPage() {
  const [buildings, setBuildings] = useState<B[]>([]);
  const [rows, setRows] = useState<Call[]>([]);
  const [bid, setBid] = useState<number | "">("");
  const [floor, setFloor] = useState(5);
  const [dir, setDir] = useState("up");
  const [pax, setPax] = useState(1);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const reload = () => api<Call[]>("/calls").then(setRows);
  useEffect(() => {
    api<B[]>("/buildings").then(b => { setBuildings(b); if (b[0]) setBid(b[0].id); });
    reload();
  }, []);
  async function create() {
    setErr(""); setMsg("");
    try {
      await api("/calls", { method: "POST", body: JSON.stringify({ building_id: bid, floor, direction: dir, passengers: pax }) });
      reload();
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  const mergeGroups = useMemo(() => {
    const m = new Map<string, Call[]>();
    for (const c of rows) {
      if (c.status !== "waiting") continue;
      const k = `${c.building_id}|${c.floor}|${c.direction}`;
      m.set(k, [...(m.get(k) ?? []), c]);
    }
    return [...m.values()].filter(g => g.length > 1);
  }, [rows]);
  async function merge(g: Call[]) {
    setErr(""); setMsg("");
    try {
      const c = await api<Call>("/calls/merge", { method: "POST", body: JSON.stringify({ call_ids: g.map(x => x.id) }) });
      setMsg(`已合并为呼梯 #${c.id}，共 ${c.passengers} 人`);
      reload();
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  const bName = (id: number) => buildings.find(b => b.id === id)?.name ?? `#${id}`;
  return (<>
    <h2>呼梯</h2>
    <div className="toolbar">
      <select value={bid} onChange={e => setBid(Number(e.target.value))}>{buildings.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}</select>
      <input type="number" value={floor} onChange={e => setFloor(Number(e.target.value))} style={{ width: 72 }} />
      <select value={dir} onChange={e => setDir(e.target.value)}><option value="up">上行</option><option value="down">下行</option></select>
      <input type="number" value={pax} min={1} onChange={e => setPax(Number(e.target.value))} style={{ width: 64 }} />
      <button onClick={create}>登记呼梯</button>
    </div>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    {mergeGroups.length > 0 && (
      <div className="merge-panel">
        <h3>可合并的同层同向候梯</h3>
        {mergeGroups.map(g => (
          <div className="merge-row" key={`${g[0].building_id}-${g[0].floor}-${g[0].direction}`}>
            <span>
              {bName(g[0].building_id)} · {g[0].floor}F · {g[0].direction === "up" ? "上行" : "下行"} ·{" "}
              {g.length} 笔共 {g.reduce((s, c) => s + c.passengers, 0)} 人（{g.map(c => `#${c.id}`).join("、")}）
            </span>
            <button onClick={() => merge(g)}>合并为一笔</button>
          </div>
        ))}
      </div>
    )}
    <table className="table"><thead><tr><th>ID</th><th>楼栋</th><th>楼层</th><th>方向</th><th>人数</th><th>状态</th><th>轿厢</th><th>评分</th></tr></thead>
    <tbody>{rows.map(c => <tr key={c.id}><td>{c.id}</td><td>{bName(c.building_id)}</td><td className="mono">{c.floor}</td><td>{c.direction}</td><td>{c.passengers}</td><td>{c.status}</td><td>{c.assigned_car_id ?? "—"}</td><td className="mono">{c.score || "—"}</td></tr>)}</tbody></table>
  </>);
}
