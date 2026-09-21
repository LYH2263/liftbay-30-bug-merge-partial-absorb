import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import BuildingsPage from "./pages/BuildingsPage";
import CarsPage from "./pages/CarsPage";
import CallsPage from "./pages/CallsPage";
import DispatchPage from "./pages/DispatchPage";
import ReplayPage from "./pages/ReplayPage";
import CongestionPage from "./pages/CongestionPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/calls" replace />} />
        <Route path="/buildings" element={<BuildingsPage />} />
        <Route path="/cars" element={<CarsPage />} />
        <Route path="/calls" element={<CallsPage />} />
        <Route path="/dispatch" element={<DispatchPage />} />
        <Route path="/replay" element={<ReplayPage />} />
        <Route path="/congestion" element={<CongestionPage />} />
      </Route>
    </Routes>
  );
}
