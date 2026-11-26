// K2 Administravimo sąsaja: šoninis meniu ir prieigos ribojimas (FR-13)
import { NavLink, Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../../auth.jsx";

export default function AdminIsdestymas() {
  const { naudotojas, yraAdmin } = useAuth();

  if (!naudotojas) return <Navigate to="/prisijungimas" replace />;
  if (!yraAdmin) {
    return <div className="pranesimas klaida" role="alert">Neturite teisės atlikti šio veiksmo.</div>;
  }

  return (
    <div className="admin">
      <nav className="sonas" aria-label="Administravimo meniu">
        <div className="sonas-antraste">Administravimas</div>
        <NavLink to="/admin/filmai">Filmai</NavLink>
        <NavLink to="/admin/seansai">Seansai ir kainos</NavLink>
        <NavLink to="/admin/sales">Salės</NavLink>
      </nav>
      <section><Outlet /></section>
    </div>
  );
}
