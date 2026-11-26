import { useEffect, useState } from "react";
import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { api } from "./api.js";
import { AuthTiekejas, useAuth } from "./auth.jsx";
import Prisijungimas from "./pages/Prisijungimas.jsx";
import AdminIsdestymas from "./pages/admin/AdminIsdestymas.jsx";
import Repertuaras from "./pages/Repertuaras.jsx";
import Filmas from "./pages/Filmas.jsx";
import SeansoSchema from "./pages/SeansoSchema.jsx";
import AdminFilmai from "./pages/admin/Filmai.jsx";
import AdminSeansai from "./pages/admin/Seansai.jsx";
import AdminSales from "./pages/admin/Sales.jsx";

function Meniu() {
  const { naudotojas, yraAdmin, atsijungti } = useAuth();
  const eiti = useNavigate();
  const atsijungtiIrGrizti = async () => {
    await atsijungti();
    eiti("/");
  };

  return (
    <nav className="meniu" aria-label="Pagrindinis meniu">
      <NavLink to="/" end>Repertuaras</NavLink>
      {yraAdmin && <NavLink to="/admin/filmai">Administravimas</NavLink>}
      {naudotojas ? (
        <>
          <span className="vardas">{naudotojas.vardas}</span>
          <button type="button" onClick={atsijungtiIrGrizti}>Atsijungti</button>
        </>
      ) : (
        <>
          <NavLink to="/prisijungimas">Prisijungti</NavLink>
          <NavLink to="/prisijungimas#registracija">Registruotis</NavLink>
        </>
      )}
    </nav>
  );
}

// NFR-10: kino teatro duomenys imami iš konfigūracijos, ne iš kodo
function Apacia() {
  const [teatras, setTeatras] = useState(null);
  useEffect(() => {
    api("/kino-teatras").then(setTeatras).catch(() => {});
  }, []);
  if (!teatras) return <footer className="apacia" />;
  return (
    <footer className="apacia">
      {teatras.pavadinimas} · {teatras.adresas} · {teatras.kontaktai}
    </footer>
  );
}

export default function App() {
  return (
    <AuthTiekejas>
      <header className="virsus">
        <NavLink to="/" className="logotipas">KinoBilietas</NavLink>
        <Meniu />
      </header>
      <main className="turinys">
        <Routes>
          <Route path="/" element={<Repertuaras />} />
          <Route path="/filmai/:id" element={<Filmas />} />
          <Route path="/seansai/:id" element={<SeansoSchema />} />
          <Route path="/prisijungimas" element={<Prisijungimas />} />
          <Route path="/admin" element={<AdminIsdestymas />}>
            <Route path="filmai" element={<AdminFilmai />} />
            <Route path="seansai" element={<AdminSeansai />} />
            <Route path="sales" element={<AdminSales />} />
            <Route path="*" element={<p className="pagalba">Pasirinkite skiltį meniu.</p>} />
          </Route>
        </Routes>
      </main>
      <Apacia />
    </AuthTiekejas>
  );
}
