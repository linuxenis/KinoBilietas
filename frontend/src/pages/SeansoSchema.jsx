// UC3.1 Pasirinkti vietas salės schemoje (FR-04, FR-05)
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";
import SalesSchema, { vietosRaktas } from "../components/SalesSchema.jsx";
import { FORMATAI, data, kaina, laikas } from "../formatas.js";

const VIETU_RIBA = 10;

export default function SeansoSchema() {
  const { id } = useParams();
  const [schema, setSchema] = useState(null);
  const [klaida, setKlaida] = useState("");
  const [pasirinktos, setPasirinktos] = useState([]);
  const [ispejimas, setIspejimas] = useState("");

  useEffect(() => {
    api(`/seansai/${id}/schema`)
      .then(setSchema)
      .catch((e) => setKlaida(e.statusas === 404 ? "Seansas nerastas arba atšauktas." : e.message));
  }, [id]);

  const keisti = (eile, vieta) => {
    if (vieta.busena !== "LAISVA") return;
    const raktas = vietosRaktas(eile.numeris, vieta.numeris);
    if (pasirinktos.some((p) => p.raktas === raktas)) {
      setPasirinktos(pasirinktos.filter((p) => p.raktas !== raktas));
      setIspejimas("");
      return;
    }
    if (pasirinktos.length >= VIETU_RIBA) {
      setIspejimas(`Vienu metu galite pasirinkti ne daugiau kaip ${VIETU_RIBA} vietų.`);
      return;
    }
    setIspejimas("");
    setPasirinktos([...pasirinktos, { raktas, eile: eile.numeris, vieta: vieta.numeris }]);
  };

  if (klaida) return <div className="pranesimas klaida">{klaida}</div>;
  if (!schema) return <p className="pagalba">Kraunama…</p>;

  const s = schema.seansas;
  const vienetas = Number(s.suaugusiojo_kaina || 0);
  const surikiuotos = [...pasirinktos].sort((a, b) => a.eile - b.eile || a.vieta - b.vieta);

  return (
    <>
      <p><Link to={`/filmai/${s.filmas_id}`}>← {s.filmas}</Link></p>
      <h1>{s.filmas}</h1>
      <p className="meta">{data(s.pradzia)} {laikas(s.pradzia)} · {s.sale} · {FORMATAI[s.formatas]}</p>
      {ispejimas && <div className="pranesimas ispejimas" role="alert">{ispejimas}</div>}

      <div className="schemos-isdestymas">
        <div className="kortele">
          <SalesSchema eiles={schema.eiles} pasirinktos={new Set(pasirinktos.map((p) => p.raktas))} onVieta={keisti} />
        </div>
        <aside className="kortele santrauka" aria-live="polite">
          <h2 style={{ marginTop: 0 }}>Pasirinktos vietos</h2>
          {surikiuotos.length === 0 ? (
            <p className="pagalba">Pažymėkite vietas schemoje (iki {VIETU_RIBA}).</p>
          ) : (
            <ul>{surikiuotos.map((p) => <li key={p.raktas}>{p.eile} eilė, {p.vieta} vieta</li>)}</ul>
          )}
          <p>Vietų: <strong>{pasirinktos.length}</strong></p>
          <p>Preliminari kaina:<br /><span className="suma">{kaina(vienetas * pasirinktos.length)}</span></p>
          <p className="pagalba">Suaugusiojo bilietas {kaina(vienetas)}. Vietų užrakinimas ir apmokėjimas įgyvendinami 2 sprinte (NI-09, NI-10).</p>
          <button type="button" className="mygtukas" disabled>Tęsti pirkimą</button>
        </aside>
      </div>
    </>
  );
}
