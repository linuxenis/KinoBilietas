// UC1: filmo informacija ir jo seansai (2.11 pav. maketas)
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";
import Plakatas from "../components/Plakatas.jsx";
import { FORMATAI, data, kaina, laikas, savaitesDiena } from "../formatas.js";

export default function Filmas() {
  const { id } = useParams();
  const [filmas, setFilmas] = useState(null);
  const [klaida, setKlaida] = useState("");

  useEffect(() => {
    api(`/filmai/${id}`).then(setFilmas).catch((e) => setKlaida(e.statusas === 404 ? "Filmas nerastas." : e.message));
  }, [id]);

  if (klaida) return <div className="pranesimas klaida">{klaida}</div>;
  if (!filmas) return <p className="pagalba">Kraunama…</p>;

  return (
    <>
      <p><Link to="/">← Repertuaras</Link></p>
      <article className="kortele filmo-eilute" style={{ gridTemplateColumns: "180px 1fr" }}>
        <Plakatas filmas={filmas} didelis />
        <div>
          <h1>{filmas.pavadinimas}</h1>
          {filmas.originalus_pavadinimas && <p className="meta">{filmas.originalus_pavadinimas}</p>}
          <p className="meta">
            <span className="cenzas">{filmas.cenzas_rodomas}</span> · {filmas.trukme_min} min · {filmas.zanrai.join(", ")}
          </p>
          {filmas.kalba && <p className="meta">Kalba: {filmas.kalba}</p>}
          {filmas.premjeros_data && <p className="meta">Premjera: {filmas.premjeros_data}</p>}
          <p>{filmas.aprasymas}</p>
        </div>
      </article>

      <h2>Seansai</h2>
      {filmas.seansai.length === 0 ? (
        <div className="pranesimas info">Artimiausioms 14 dienų seansų nėra.</div>
      ) : (
        <div className="kortele lenteles-apvalkalas">
          <table className="lentele">
            <thead>
              <tr><th>Data</th><th>Laikas</th><th>Salė</th><th>Formatas</th><th>Kaina nuo</th><th>Laisvos vietos</th><th></th></tr>
            </thead>
            <tbody>
              {filmas.seansai.map((s) => (
                <tr key={s.id}>
                  <td>{data(s.pradzia)} ({savaitesDiena(data(s.pradzia))})</td>
                  <td><strong>{laikas(s.pradzia)}</strong></td>
                  <td>{s.sale}</td>
                  <td>{FORMATAI[s.formatas]}</td>
                  <td>{kaina(s.maziausia_kaina)}</td>
                  <td>{s.laisvos_vietos}</td>
                  <td><Link className="mygtukas" to={`/seansai/${s.id}`}>Rinktis vietas</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
