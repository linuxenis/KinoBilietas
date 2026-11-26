// UC1 Peržiūrėti repertuarą ir seansus (2.10 pav. maketas)
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import Plakatas from "../components/Plakatas.jsx";
import SeansoMygtukas from "../components/SeansoMygtukas.jsx";
import { CENZAI, pridetiDienu, savaitesDiena, siandien } from "../formatas.js";

const DIENOS = 14;

// Individualizavimas: paskutinė data ir filtrai įsimenami naršyklės sesijoje
function isSesijos(raktas, numatyta) {
  try {
    return sessionStorage.getItem(raktas) || numatyta;
  } catch {
    return numatyta;
  }
}
function iSesija(raktas, reiksme) {
  try {
    sessionStorage.setItem(raktas, reiksme);
  } catch {
    /* nesaugoma */
  }
}

export default function Repertuaras() {
  const sDiena = siandien();
  const datos = Array.from({ length: DIENOS }, (_, i) => pridetiDienu(sDiena, i));
  const issaugotaData = isSesijos("rep_data", sDiena);
  const [data, setData] = useState(datos.includes(issaugotaData) ? issaugotaData : sDiena);
  const [zanras, setZanras] = useState(isSesijos("rep_zanras", "visi"));
  const [sale, setSale] = useState(isSesijos("rep_sale", "visi"));
  const [zanrai, setZanrai] = useState([]);
  const [sales, setSales] = useState([]);
  const [atsakas, setAtsakas] = useState(null);
  const [klaida, setKlaida] = useState("");

  useEffect(() => {
    api("/zanrai").then(setZanrai).catch(() => {});
    api("/sales").then(setSales).catch(() => {});
  }, []);

  useEffect(() => {
    iSesija("rep_data", data);
    iSesija("rep_zanras", zanras);
    iSesija("rep_sale", sale);
    setKlaida("");
    api(`/seansai?data=${data}&zanras=${zanras}&sale=${sale}`)
      .then(setAtsakas)
      .catch((e) => setKlaida(e.message));
  }, [data, zanras, sale]);

  const yraFiltru = zanras !== "visi" || sale !== "visi";

  return (
    <>
      <h1>Repertuaras</h1>
      <div className="datos" role="tablist" aria-label="Data">
        {datos.map((d, i) => (
          <button key={d} role="tab" aria-selected={d === data} className={d === data ? "aktyvi" : ""} onClick={() => setData(d)}>
            {i === 0 ? "Šiandien" : savaitesDiena(d)}
            <small>{d.slice(5)}</small>
          </button>
        ))}
      </div>

      <div className="filtrai">
        <div className="laukas">
          <label htmlFor="f-zanras">Žanras</label>
          <select id="f-zanras" value={zanras} onChange={(e) => setZanras(e.target.value)}>
            <option value="visi">Visi</option>
            {zanrai.map((z) => <option key={z.id} value={z.id}>{z.pavadinimas}</option>)}
          </select>
        </div>
        <div className="laukas">
          <label htmlFor="f-sale">Salė</label>
          <select id="f-sale" value={sale} onChange={(e) => setSale(e.target.value)}>
            <option value="visi">Visos</option>
            {sales.map((s) => <option key={s.id} value={s.id}>{s.pavadinimas}</option>)}
          </select>
        </div>
      </div>

      {klaida && <div className="pranesimas klaida">{klaida}</div>}
      {!atsakas && !klaida && <p className="pagalba">Kraunama…</p>}
      {atsakas && atsakas.filmai.length === 0 && (
        <div className="pranesimas info" role="status">
          {yraFiltru ? "Pagal pasirinktus filtrus seansų nėra." : "Šią dieną seansų nebėra."}
          {atsakas.artimiausia_data && (
            <>
              {" "}Artimiausias seansas:{" "}
              <button type="button" className="mygtukas antrinis" onClick={() => setData(atsakas.artimiausia_data)}>
                {atsakas.artimiausia_data}
              </button>
            </>
          )}
        </div>
      )}

      {atsakas?.filmai.map((f) => (
        <article key={f.id} className="kortele filmo-eilute">
          <Link to={`/filmai/${f.id}`} tabIndex={-1}><Plakatas filmas={f} /></Link>
          <div>
            <h2 className="filmo-pavadinimas"><Link to={`/filmai/${f.id}`}>{f.pavadinimas}</Link></h2>
            <p className="meta">
              <span className="cenzas">{CENZAI[f.cenzas]}</span> · {f.trukme_min} min · {f.zanrai.join(", ")}
            </p>
            <div className="seansai">
              {f.seansai.map((s) => <SeansoMygtukas key={s.id} seansas={s} />)}
            </div>
          </div>
        </article>
      ))}
    </>
  );
}
