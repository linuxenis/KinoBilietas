// UC6.1 Tvarkyti filmus (FR-06, 2.14 pav. maketas)
import { useCallback, useEffect, useState } from "react";
import { api } from "../../api.js";
import Pranesimas from "../../components/Pranesimas.jsx";
import { CENZAI } from "../../formatas.js";

const TUSCIA = {
  pavadinimas: "", originalus_pavadinimas: "", trukme_min: "", cenzas: "", zanrai: [],
  aprasymas: "", premjeros_data: "", kalba: "", platintojas: "",
};

function tikrinti(f) {
  const k = {};
  if (!f.pavadinimas.trim()) k.pavadinimas = "Įveskite filmo pavadinimą.";
  const t = Number(f.trukme_min);
  if (!f.trukme_min || !Number.isInteger(t) || t < 1 || t > 400) k.trukme_min = "Trukmė turi būti nuo 1 iki 400 min.";
  if (!f.cenzas) k.cenzas = "Pasirinkite amžiaus cenzą.";
  if (f.zanrai.length === 0) k.zanrai = "Pasirinkite bent vieną žanrą.";
  if (!f.platintojas) k.platintojas = "Pasirinkite platintoją.";
  if (f.premjeros_data && !/^\d{4}-\d{2}-\d{2}$/.test(f.premjeros_data)) k.premjeros_data = "Data turi būti formatu MMMM-MM-DD.";
  if (f.aprasymas.length > 2000) k.aprasymas = "Aprašymas negali būti ilgesnis nei 2000 simbolių.";
  return k;
}

function FilmoForma({ pradinis, zanrai, platintojai, issaugota, atsaukti }) {
  const [f, setF] = useState(() => (pradinis ? { ...TUSCIA, ...pradinis, premjeros_data: pradinis.premjeros_data || "" } : TUSCIA));
  const [plakatas, setPlakatas] = useState(null);
  const [klaidos, setKlaidos] = useState({});
  const [siunciama, setSiunciama] = useState(false);
  const keisti = (laukas) => (e) => setF({ ...f, [laukas]: e.target.value });
  const zanras = (id) => (e) =>
    setF({ ...f, zanrai: e.target.checked ? [...f.zanrai, id] : f.zanrai.filter((z) => z !== id) });

  const pateikti = async (e) => {
    e.preventDefault();
    const k = tikrinti(f);
    if (plakatas && plakatas.size > 2 * 1024 * 1024) k.plakatas = "Plakatas negali būti didesnis nei 2 MB.";
    setKlaidos(k);
    if (Object.keys(k).length) return;

    const duomenys = new FormData();
    for (const laukas of ["pavadinimas", "originalus_pavadinimas", "trukme_min", "cenzas", "aprasymas", "kalba", "platintojas"]) {
      duomenys.append(laukas, f[laukas] ?? "");
    }
    if (f.premjeros_data) duomenys.append("premjeros_data", f.premjeros_data);
    f.zanrai.forEach((z) => duomenys.append("zanrai", z));
    if (plakatas) duomenys.append("plakatas", plakatas);

    setSiunciama(true);
    try {
      const rez = await api(pradinis ? `/filmai/${pradinis.id}` : "/filmai", { metodas: pradinis ? "PUT" : "POST", kunas: duomenys });
      issaugota(rez);
    } catch (err) {
      const is = {};
      for (const [laukas, z] of Object.entries(err.duomenys || {})) is[laukas] = Array.isArray(z) ? z[0] : z;
      setKlaidos(Object.keys(is).length ? is : { bendra: "Nepavyko išsaugoti filmo." });
    } finally {
      setSiunciama(false);
    }
  };

  const laukoKlase = (l) => `laukas${klaidos[l] ? " klaidingas" : ""}`;
  const Klaida = ({ l }) => (klaidos[l] ? <span className="lauko-klaida" role="alert">{klaidos[l]}</span> : null);

  return (
    <form className="kortele forma" onSubmit={pateikti} noValidate>
      <h2 style={{ marginTop: 0 }}>{pradinis ? `Redaguoti: ${pradinis.pavadinimas}` : "Naujas filmas"}</h2>
      {klaidos.bendra && <div className="pranesimas klaida">{klaidos.bendra}</div>}
      <div className="eilute">
        <div className={laukoKlase("pavadinimas")}>
          <label htmlFor="f-pav">Pavadinimas *</label>
          <input id="f-pav" maxLength={200} value={f.pavadinimas} onChange={keisti("pavadinimas")} />
          <Klaida l="pavadinimas" />
        </div>
        <div className="laukas">
          <label htmlFor="f-orig">Originalus pavadinimas</label>
          <input id="f-orig" maxLength={200} value={f.originalus_pavadinimas} onChange={keisti("originalus_pavadinimas")} />
        </div>
      </div>
      <div className="eilute">
        <div className={laukoKlase("trukme_min")}>
          <label htmlFor="f-truk">Trukmė, min *</label>
          <input id="f-truk" type="number" min={1} max={400} value={f.trukme_min} onChange={keisti("trukme_min")} />
          <Klaida l="trukme_min" />
        </div>
        <div className={laukoKlase("cenzas")}>
          <label htmlFor="f-cenz">Amžiaus cenzas *</label>
          <select id="f-cenz" value={f.cenzas} onChange={keisti("cenzas")}>
            <option value="">Pasirinkite</option>
            {Object.entries(CENZAI).map(([r, t]) => <option key={r} value={r}>{t}</option>)}
          </select>
          <Klaida l="cenzas" />
        </div>
        <div className={laukoKlase("platintojas")}>
          <label htmlFor="f-plat">Platintojas *</label>
          <select id="f-plat" value={f.platintojas} onChange={keisti("platintojas")}>
            <option value="">Pasirinkite</option>
            {platintojai.map((p) => <option key={p.id} value={p.id}>{p.pavadinimas}</option>)}
          </select>
          <Klaida l="platintojas" />
        </div>
      </div>
      <fieldset className={laukoKlase("zanrai")} style={{ border: 0, padding: 0, margin: 0 }}>
        <legend style={{ fontWeight: 600, fontSize: "0.92rem", marginBottom: "0.25rem" }}>Žanrai *</legend>
        <div className="varneles">
          {zanrai.map((z) => (
            <label key={z.id}>
              <input type="checkbox" checked={f.zanrai.includes(z.id)} onChange={zanras(z.id)} /> {z.pavadinimas}
            </label>
          ))}
        </div>
        <Klaida l="zanrai" />
      </fieldset>
      <div className={laukoKlase("aprasymas")}>
        <label htmlFor="f-apr">Aprašymas</label>
        <textarea id="f-apr" rows={4} maxLength={2000} value={f.aprasymas} onChange={keisti("aprasymas")} />
        <span className="pagalba">{f.aprasymas.length} / 2000</span>
        <Klaida l="aprasymas" />
      </div>
      <div className="eilute">
        <div className={laukoKlase("premjeros_data")}>
          <label htmlFor="f-prem">Premjeros data</label>
          <input id="f-prem" inputMode="numeric" placeholder="MMMM-MM-DD" maxLength={10} value={f.premjeros_data} onChange={keisti("premjeros_data")} />
          <Klaida l="premjeros_data" />
        </div>
        <div className="laukas">
          <label htmlFor="f-kalba">Kalba ir subtitrai</label>
          <input id="f-kalba" value={f.kalba} onChange={keisti("kalba")} />
        </div>
        <div className={laukoKlase("plakatas")}>
          <label htmlFor="f-plak">Plakatas (JPG, PNG, iki 2 MB)</label>
          <input id="f-plak" type="file" accept="image/jpeg,image/png" onChange={(e) => setPlakatas(e.target.files[0] || null)} />
          <Klaida l="plakatas" />
        </div>
      </div>
      <div className="veiksmai">
        <button className="mygtukas" disabled={siunciama}>Išsaugoti</button>
        <button type="button" className="mygtukas antrinis" onClick={atsaukti}>Atšaukti</button>
      </div>
    </form>
  );
}

export default function Filmai() {
  const [filmai, setFilmai] = useState([]);
  const [zanrai, setZanrai] = useState([]);
  const [platintojai, setPlatintojai] = useState([]);
  const [redaguojamas, setRedaguojamas] = useState(undefined); // undefined: forma uždaryta, null: naujas
  const [salinamas, setSalinamas] = useState(null);
  const [pranesimas, setPranesimas] = useState(null);
  const [kiekis, setKiekis] = useState(10);
  const uzdaryti = useCallback(() => setPranesimas(null), []);

  const ikelti = () => api("/filmai").then(setFilmai);
  useEffect(() => {
    ikelti();
    api("/zanrai").then(setZanrai);
    api("/platintojai").then(setPlatintojai);
  }, []);

  const issaugota = (f) => {
    setRedaguojamas(undefined);
    setPranesimas({ tipas: "sekme", tekstas: `Filmas „${f.pavadinimas}“ išsaugotas.` });
    ikelti();
  };

  const salinti = async (f) => {
    try {
      await api(`/filmai/${f.id}`, { metodas: "DELETE" });
      setPranesimas({ tipas: "sekme", tekstas: `Filmas „${f.pavadinimas}“ pašalintas.` });
      ikelti();
    } catch (err) {
      setPranesimas({ tipas: "klaida", tekstas: err.duomenys?.klaida || "Nepavyko pašalinti filmo." });
    }
    setSalinamas(null);
  };

  const zanruPavadinimai = (ids) => zanrai.filter((z) => ids.includes(z.id)).map((z) => z.pavadinimas).join(", ");

  return (
    <>
      <div className="eilute" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0 }}>Filmai</h1>
        {redaguojamas === undefined && (
          <button className="mygtukas" onClick={() => { setPranesimas(null); setRedaguojamas(null); }}>+ Naujas filmas</button>
        )}
      </div>
      <div style={{ height: "0.75rem" }} />
      <Pranesimas pranesimas={pranesimas} uzdaryti={uzdaryti} />

      {redaguojamas !== undefined && (
        <FilmoForma key={redaguojamas?.id ?? "naujas"} pradinis={redaguojamas} zanrai={zanrai} platintojai={platintojai}
          issaugota={issaugota} atsaukti={() => setRedaguojamas(undefined)} />
      )}

      <div className="kortele lenteles-apvalkalas">
        <table className="lentele">
          <thead>
            <tr><th>Pavadinimas</th><th>Trukmė</th><th>Cenzas</th><th>Žanrai</th><th>Veiksmai</th></tr>
          </thead>
          <tbody>
            {filmai.slice(0, kiekis).map((f) => (
              <tr key={f.id}>
                <td><strong>{f.pavadinimas}</strong></td>
                <td>{f.trukme_min} min</td>
                <td>{CENZAI[f.cenzas]}</td>
                <td>{zanruPavadinimai(f.zanrai)}</td>
                <td>
                  {salinamas === f.id ? (
                    <span className="veiksmai">
                      Šalinti?
                      <button className="mygtukas pavojingas" onClick={() => salinti(f)}>Taip</button>
                      <button className="mygtukas antrinis" onClick={() => setSalinamas(null)}>Ne</button>
                    </span>
                  ) : (
                    <span className="veiksmai">
                      <button className="mygtukas antrinis" onClick={() => { setPranesimas(null); setRedaguojamas(f); }}>Redaguoti</button>
                      <button className="mygtukas pavojingas" onClick={() => setSalinamas(f.id)}>Šalinti</button>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="eilute" style={{ marginTop: "0.75rem", alignItems: "center" }}>
          <label htmlFor="kiekis" className="pagalba">Rodyti įrašų:</label>
          <select id="kiekis" value={kiekis} onChange={(e) => setKiekis(Number(e.target.value))}>
            {[10, 25, 50].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
          <span className="pagalba">Iš viso: {filmai.length}</span>
        </div>
      </div>
    </>
  );
}
