// UC9 Užsiregistruoti, UC10 Prisijungti (2.13 pav. maketas)
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

function Laukas({ id, etikete, klaida, pagalba, ...kita }) {
  return (
    <div className={`laukas${klaida ? " klaidingas" : ""}`}>
      <label htmlFor={id}>{etikete}</label>
      <input id={id} aria-invalid={!!klaida} {...kita} />
      {pagalba && <span className="pagalba">{pagalba}</span>}
      {klaida && <span className="lauko-klaida" role="alert">{klaida}</span>}
    </div>
  );
}

function PrisijungimoForma() {
  const { prisijungti } = useAuth();
  const eiti = useNavigate();
  const [email, setEmail] = useState("");
  const [slaptazodis, setSlaptazodis] = useState("");
  const [klaida, setKlaida] = useState("");
  const [siunciama, setSiunciama] = useState(false);

  const pateikti = async (e) => {
    e.preventDefault();
    setKlaida("");
    setSiunciama(true);
    try {
      const n = await prisijungti(email, slaptazodis);
      eiti(n.role === "ADMINISTRATORIUS" ? "/admin/filmai" : "/");
    } catch (err) {
      setKlaida(err.duomenys?.klaida || "Nepavyko prisijungti. Bandykite dar kartą.");
    } finally {
      setSiunciama(false);
    }
  };

  return (
    <form className="kortele forma" onSubmit={pateikti} noValidate>
      <h2>Prisijungti</h2>
      {klaida && <div className="pranesimas klaida" role="alert">{klaida}</div>}
      <Laukas id="p-email" etikete="El. paštas" type="email" autoComplete="email"
        value={email} onChange={(e) => setEmail(e.target.value)} required />
      <Laukas id="p-slaptazodis" etikete="Slaptažodis" type="password" autoComplete="current-password"
        value={slaptazodis} onChange={(e) => setSlaptazodis(e.target.value)} required />
      <div><button className="mygtukas" disabled={siunciama || !email || !slaptazodis}>Prisijungti</button></div>
    </form>
  );
}

function tikrintiRegistracija(d) {
  const k = {};
  if (!d.vardas.trim()) k.vardas = "Įveskite vardą.";
  else if (d.vardas.length > 50) k.vardas = "Vardas negali būti ilgesnis nei 50 simbolių.";
  if (!/^\S+@\S+\.\S+$/.test(d.email)) k.email = "Įveskite galiojantį el. pašto adresą.";
  if (d.slaptazodis.length < 8 || !/\p{L}/u.test(d.slaptazodis) || !/\d/.test(d.slaptazodis))
    k.slaptazodis = "Slaptažodį turi sudaryti bent 8 simboliai, bent viena raidė ir vienas skaitmuo.";
  if (d.slaptazodis !== d.slaptazodis2) k.slaptazodis2 = "Slaptažodžiai nesutampa.";
  if (!d.sutikimas) k.sutikimas = "Norėdami užsiregistruoti, sutikite su privatumo politika.";
  return k;
}

function RegistracijosForma() {
  const { registruotis } = useAuth();
  const eiti = useNavigate();
  const [d, setD] = useState({ vardas: "", email: "", slaptazodis: "", slaptazodis2: "", sutikimas: false });
  const [klaidos, setKlaidos] = useState({});
  const [siunciama, setSiunciama] = useState(false);
  const keisti = (laukas) => (e) =>
    setD({ ...d, [laukas]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  const pateikti = async (e) => {
    e.preventDefault();
    const k = tikrintiRegistracija(d);
    setKlaidos(k);
    if (Object.keys(k).length) return;
    setSiunciama(true);
    try {
      await registruotis(d);
      eiti("/");
    } catch (err) {
      const s = err.duomenys || {};
      const is = {};
      for (const [laukas, zinute] of Object.entries(s)) is[laukas] = Array.isArray(zinute) ? zinute[0] : zinute;
      setKlaidos(Object.keys(is).length ? is : { bendra: "Nepavyko užsiregistruoti." });
    } finally {
      setSiunciama(false);
    }
  };

  return (
    <form id="registracija" className="kortele forma" onSubmit={pateikti} noValidate>
      <h2>Registruotis</h2>
      {klaidos.bendra && <div className="pranesimas klaida">{klaidos.bendra}</div>}
      <Laukas id="r-vardas" etikete="Vardas *" value={d.vardas} onChange={keisti("vardas")} klaida={klaidos.vardas} maxLength={50} />
      <Laukas id="r-email" etikete="El. paštas *" type="email" autoComplete="email" value={d.email} onChange={keisti("email")} klaida={klaidos.email} />
      <Laukas id="r-slaptazodis" etikete="Slaptažodis *" type="password" autoComplete="new-password"
        value={d.slaptazodis} onChange={keisti("slaptazodis")} klaida={klaidos.slaptazodis}
        pagalba="Bent 8 simboliai, bent viena raidė ir vienas skaitmuo." />
      <Laukas id="r-slaptazodis2" etikete="Pakartokite slaptažodį *" type="password" autoComplete="new-password"
        value={d.slaptazodis2} onChange={keisti("slaptazodis2")} klaida={klaidos.slaptazodis2} />
      <div className={`laukas${klaidos.sutikimas ? " klaidingas" : ""}`}>
        <label style={{ fontWeight: 400, display: "flex", gap: "0.4rem" }}>
          <input type="checkbox" checked={d.sutikimas} onChange={keisti("sutikimas")} />
          Sutinku su privatumo politika *
        </label>
        {klaidos.sutikimas && <span className="lauko-klaida" role="alert">{klaidos.sutikimas}</span>}
      </div>
      <p className="pagalba">Renkame tik vardą ir el. paštą (BDAR).</p>
      <div><button className="mygtukas" disabled={siunciama}>Registruotis</button></div>
    </form>
  );
}

export default function Prisijungimas() {
  return (
    <>
      <h1>Paskyra</h1>
      <div className="prisijungimas">
        <PrisijungimoForma />
        <RegistracijosForma />
      </div>
    </>
  );
}
