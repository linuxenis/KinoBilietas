// UC6.2 Tvarkyti seansus ir kainas (FR-07, FR-08, 2.15 pav. maketas)
import { useCallback, useEffect, useState } from "react";
import { api } from "../../api.js";
import Pranesimas from "../../components/Pranesimas.jsx";
import { FORMATAI, data, kaina, laikas, pridetiDienu, savaitesDiena, siandien } from "../../formatas.js";

const PARUOSIMAS_MIN = 15;

function pabaigosLaikas(pradzia, trukme) {
  if (!pradzia || !trukme) return "";
  const [v, m] = pradzia.split(":").map(Number);
  const viso = v * 60 + m + Number(trukme) + PARUOSIMAS_MIN;
  const kitaDiena = viso >= 24 * 60 ? " (kitą dieną)" : "";
  const min = viso % (24 * 60);
  return `${String(Math.floor(min / 60)).padStart(2, "0")}:${String(min % 60).padStart(2, "0")}${kitaDiena}`;
}

function tusciaForma(data) {
  return {
    filmas: "", sale: "", data, pradzia: "", formatas: "F2D",
    kaina_suaugusiojo: "", kaina_studento: "", kaina_senjoro: "",
  };
}

function isSeanso(s) {
  return {
    filmas: s.filmas, sale: s.sale, data: data(s.pradzia),
    pradzia: laikas(s.pradzia), formatas: s.formatas,
    kaina_suaugusiojo: s.kaina_suaugusiojo ?? "", kaina_studento: s.kaina_studento ?? "", kaina_senjoro: s.kaina_senjoro ?? "",
  };
}

function tikrinti(f) {
  const k = {};
  if (!f.filmas) k.filmas = "Pasirinkite filmą.";
  if (!f.sale) k.sale = "Pasirinkite salę.";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(f.data)) k.data = "Data turi būti formatu MMMM-MM-DD.";
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(f.pradzia)) k.pradzia = "Laikas turi būti formatu VV:MM.";
  const kainosKlaida = (r) => {
    const n = Number(String(r).replace(",", "."));
    return Number.isNaN(n) || n < 0.01 || n > 99.99 ? "Kaina turi būti nuo 0,01 iki 99,99 €." : null;
  };
  if (f.kaina_suaugusiojo === "") k.kaina_suaugusiojo = "Įveskite suaugusiojo bilieto kainą.";
  else if (kainosKlaida(f.kaina_suaugusiojo)) k.kaina_suaugusiojo = kainosKlaida(f.kaina_suaugusiojo);
  for (const l of ["kaina_studento", "kaina_senjoro"]) if (f[l] !== "" && kainosKlaida(f[l])) k[l] = kainosKlaida(f[l]);
  return k;
}

function SeansoForma({ pradinis, filmai, sales, numatytaData, issaugota, atsaukti }) {
  const [f, setF] = useState(() => (pradinis ? isSeanso(pradinis) : tusciaForma(numatytaData)));
  const [klaidos, setKlaidos] = useState({});
  const [siunciama, setSiunciama] = useState(false);
  const keisti = (l) => (e) => setF({ ...f, [l]: e.target.value });
  const filmas = filmai.find((x) => String(x.id) === String(f.filmas));

  const pateikti = async (e) => {
    e.preventDefault();
    const k = tikrinti(f);
    setKlaidos(k);
    if (Object.keys(k).length) return;
    const kaina = (r) => (r === "" ? null : String(r).replace(",", "."));
    const kunas = {
      ...f, filmas: Number(f.filmas), sale: Number(f.sale),
      kaina_suaugusiojo: kaina(f.kaina_suaugusiojo), kaina_studento: kaina(f.kaina_studento), kaina_senjoro: kaina(f.kaina_senjoro),
    };
    setSiunciama(true);
    try {
      const rez = await api(pradinis ? `/seansai/${pradinis.id}` : "/seansai", { metodas: pradinis ? "PUT" : "POST", kunas });
      issaugota(rez);
    } catch (err) {
      const is = {};
      for (const [l, z] of Object.entries(err.duomenys || {})) if (z) is[l] = Array.isArray(z) ? z[0] : z;
      setKlaidos(Object.keys(is).length ? is : { bendra: "Nepavyko išsaugoti seanso." });
    } finally {
      setSiunciama(false);
    }
  };

  const kl = (l) => `laukas${klaidos[l] ? " klaidingas" : ""}`;
  const Klaida = ({ l }) => (klaidos[l] ? <span className="lauko-klaida" role="alert">{klaidos[l]}</span> : null);

  return (
    <form className="kortele forma" onSubmit={pateikti} noValidate>
      <h2 style={{ marginTop: 0 }}>{pradinis ? "Redaguoti seansą" : "Naujas seansas"}</h2>
      <div className="eilute">
        <div className={kl("filmas")}>
          <label htmlFor="s-filmas">Filmas *</label>
          <select id="s-filmas" value={f.filmas} onChange={keisti("filmas")}>
            <option value="">Pasirinkite</option>
            {filmai.map((x) => <option key={x.id} value={x.id}>{x.pavadinimas} ({x.trukme_min} min)</option>)}
          </select>
          <Klaida l="filmas" />
        </div>
        <div className={kl("sale")}>
          <label htmlFor="s-sale">Salė *</label>
          <select id="s-sale" value={f.sale} onChange={keisti("sale")}>
            <option value="">Pasirinkite</option>
            {sales.map((x) => <option key={x.id} value={x.id}>{x.pavadinimas}</option>)}
          </select>
          <Klaida l="sale" />
        </div>
      </div>
      <div className="eilute">
        <div className={kl("data")}>
          <label htmlFor="s-data">Data *</label>
          <input id="s-data" inputMode="numeric" placeholder="MMMM-MM-DD" maxLength={10} value={f.data} onChange={keisti("data")} />
          <Klaida l="data" />
        </div>
        <div className={kl("pradzia")}>
          <label htmlFor="s-pradzia">Pradžia *</label>
          <input id="s-pradzia" inputMode="numeric" placeholder="VV:MM" maxLength={5} value={f.pradzia} onChange={keisti("pradzia")} />
          <Klaida l="pradzia" />
        </div>
        <div className="laukas">
          <label htmlFor="s-pabaiga">Pabaiga</label>
          <input id="s-pabaiga" readOnly value={pabaigosLaikas(f.pradzia, filmas?.trukme_min)} placeholder="Apskaičiuojama" />
          <span className="pagalba">Trukmė + {PARUOSIMAS_MIN} min salės paruošimui.</span>
        </div>
        <div className="laukas">
          <label htmlFor="s-formatas">Formatas</label>
          <select id="s-formatas" value={f.formatas} onChange={keisti("formatas")}>
            {Object.entries(FORMATAI).map(([r, t]) => <option key={r} value={r}>{t}</option>)}
          </select>
        </div>
      </div>
      <div className="eilute">
        <div className={kl("kaina_suaugusiojo")}>
          <label htmlFor="s-k1">Suaugusiojo kaina, € *</label>
          <input id="s-k1" inputMode="decimal" value={f.kaina_suaugusiojo} onChange={keisti("kaina_suaugusiojo")} placeholder="6,50" />
          <Klaida l="kaina_suaugusiojo" />
        </div>
        <div className={kl("kaina_studento")}>
          <label htmlFor="s-k2">Studento kaina, €</label>
          <input id="s-k2" inputMode="decimal" value={f.kaina_studento} onChange={keisti("kaina_studento")} placeholder="5,00" />
          <Klaida l="kaina_studento" />
        </div>
        <div className={kl("kaina_senjoro")}>
          <label htmlFor="s-k3">Senjoro kaina, €</label>
          <input id="s-k3" inputMode="decimal" value={f.kaina_senjoro} onChange={keisti("kaina_senjoro")} placeholder="4,50" />
          <Klaida l="kaina_senjoro" />
        </div>
      </div>
      {klaidos.bendra && <div className="pranesimas klaida" role="alert">{klaidos.bendra}</div>}
      <div className="veiksmai">
        <button className="mygtukas" disabled={siunciama}>Išsaugoti</button>
        <button type="button" className="mygtukas antrinis" onClick={atsaukti}>Atšaukti</button>
      </div>
    </form>
  );
}

export default function Seansai() {
  const [diena, setDiena] = useState(siandien());
  const [seansai, setSeansai] = useState([]);
  const [filmai, setFilmai] = useState([]);
  const [sales, setSales] = useState([]);
  const [forma, setForma] = useState(undefined); // undefined uždaryta, null naujas
  const [atsaukiamas, setAtsaukiamas] = useState(null);
  const [pranesimas, setPranesimas] = useState(null);
  const uzdaryti = useCallback(() => setPranesimas(null), []);

  const ikelti = useCallback(() => api(`/seansai/valdymas?data=${diena}`).then(setSeansai), [diena]);
  useEffect(() => { ikelti(); }, [ikelti]);
  useEffect(() => {
    api("/filmai").then(setFilmai);
    api("/sales").then(setSales);
  }, []);

  const issaugota = (s) => {
    setForma(undefined);
    setPranesimas({ tipas: "sekme", tekstas: `Seansas „${s.filmo_pavadinimas}“ ${laikas(s.pradzia)} išsaugotas ir paskelbtas repertuare.` });
    ikelti();
  };

  const atsaukti = async (s) => {
    await api(`/seansai/${s.id}/atsaukti`, { metodas: "POST" });
    setAtsaukiamas(null);
    setPranesimas({ tipas: "sekme", tekstas: `Seansas „${s.filmo_pavadinimas}“ ${laikas(s.pradzia)} atšauktas.` });
    ikelti();
  };

  return (
    <>
      <div className="eilute" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0 }}>Seansai ir kainos</h1>
        {forma === undefined && <button className="mygtukas" onClick={() => setForma(null)}>+ Naujas seansas</button>}
      </div>
      <div style={{ height: "0.75rem" }} />
      <Pranesimas pranesimas={pranesimas} uzdaryti={uzdaryti} />
      {forma !== undefined && (
        <SeansoForma key={forma?.id ?? "naujas"} pradinis={forma} filmai={filmai} sales={sales} numatytaData={diena}
          issaugota={issaugota} atsaukti={() => setForma(undefined)} />
      )}

      <div className="kortele">
        <div className="eilute" style={{ alignItems: "center", marginBottom: "0.75rem" }}>
          <button className="mygtukas antrinis" onClick={() => setDiena(pridetiDienu(diena, -1))} aria-label="Ankstesnė diena">←</button>
          <strong aria-live="polite">{diena} ({savaitesDiena(diena)})</strong>
          <button className="mygtukas antrinis" onClick={() => setDiena(pridetiDienu(diena, 1))} aria-label="Kita diena">→</button>
        </div>
        <div className="lenteles-apvalkalas">
          <table className="lentele">
            <thead>
              <tr><th>Salė</th><th>Laikas</th><th>Filmas</th><th>Formatas</th><th>Kainos</th><th>Būsena</th><th>Veiksmai</th></tr>
            </thead>
            <tbody>
              {seansai.length === 0 && <tr><td colSpan={7} className="pagalba">Šią dieną seansų nėra.</td></tr>}
              {seansai.map((s) => {
                const atsauktas = s.busena === "ATSAUKTAS";
                const praeityje = new Date(s.pradzia) <= new Date();
                return (
                  <tr key={s.id} style={atsauktas ? { color: "var(--blankus)", textDecoration: "line-through" } : undefined}>
                    <td>{s.sales_pavadinimas}</td>
                    <td><strong>{laikas(s.pradzia)}</strong>–{laikas(s.pabaiga)}</td>
                    <td>{s.filmo_pavadinimas}</td>
                    <td>{FORMATAI[s.formatas]}</td>
                    <td>{[s.kaina_suaugusiojo, s.kaina_studento, s.kaina_senjoro].filter(Boolean).map(kaina).join(" / ")}</td>
                    <td>{atsauktas ? "Atšauktas" : praeityje ? "Įvykęs" : "Suplanuotas"}</td>
                    <td>
                      {!atsauktas && !praeityje && (atsaukiamas === s.id ? (
                        <span className="veiksmai">
                          Atšaukti?
                          <button className="mygtukas pavojingas" onClick={() => atsaukti(s)}>Taip</button>
                          <button className="mygtukas antrinis" onClick={() => setAtsaukiamas(null)}>Ne</button>
                        </span>
                      ) : (
                        <span className="veiksmai">
                          <button className="mygtukas antrinis" onClick={() => setForma(s)}>Redaguoti</button>
                          <button className="mygtukas pavojingas" onClick={() => setAtsaukiamas(s.id)}>Atšaukti seansą</button>
                        </span>
                      ))}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
