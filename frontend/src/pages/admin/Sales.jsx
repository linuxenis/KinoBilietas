// UC6.3 Tvarkyti sales (FR-09, 2.16 pav. maketas)
import { useCallback, useEffect, useState } from "react";
import { api } from "../../api.js";
import Pranesimas from "../../components/Pranesimas.jsx";
import SalesSchema, { vietosRaktas } from "../../components/SalesSchema.jsx";
import { vietos as vietuTekstas } from "../../formatas.js";

// Spustelėjus vietą jos tipas keičiamas ratu
const KITAS_TIPAS = { STANDARTINE: "NEIGALIESIEMS", NEIGALIESIEMS: "NEPRIEINAMA", NEPRIEINAMA: "STANDARTINE" };

function isSchemos(eiles) {
  const tipai = {};
  for (const e of eiles) {
    for (const v of e.vietos) {
      const t = v.busena === "NEPRIEINAMA" ? "NEPRIEINAMA" : v.tipas;
      if (t !== "STANDARTINE") tipai[vietosRaktas(e.numeris, v.numeris)] = t;
    }
  }
  return tipai;
}

function SalesRedaktorius({ pradine, issaugota, atsaukti }) {
  const [pavadinimas, setPavadinimas] = useState(pradine?.pavadinimas ?? "");
  const [eiliu, setEiliu] = useState(pradine?.eiliu ?? 8);
  const [vietu, setVietu] = useState(pradine?.vietu ?? 10);
  const [tipai, setTipai] = useState(() => (pradine ? isSchemos(pradine.eiles) : {}));
  const [klaidos, setKlaidos] = useState({});
  const [siunciama, setSiunciama] = useState(false);
  const uzrakinta = pradine?.turi_busimu_seansu;

  const e = Math.min(Math.max(Number(eiliu) || 0, 0), 30);
  const v = Math.min(Math.max(Number(vietu) || 0, 0), 40);
  const eiles = Array.from({ length: e }, (_, i) => ({
    numeris: i + 1,
    vietos: Array.from({ length: v }, (_, j) => {
      const t = tipai[vietosRaktas(i + 1, j + 1)] || "STANDARTINE";
      return { numeris: j + 1, tipas: t === "NEIGALIESIEMS" ? "NEIGALIESIEMS" : "STANDARTINE", busena: t === "NEPRIEINAMA" ? "NEPRIEINAMA" : "LAISVA" };
    }),
  }));
  const neprieinamu = eiles.reduce((s, x) => s + x.vietos.filter((y) => y.busena === "NEPRIEINAMA").length, 0);
  const talpa = e * v - neprieinamu;

  const keistiVieta = (eile, vieta) => {
    const r = vietosRaktas(eile.numeris, vieta.numeris);
    const dabar = tipai[r] || "STANDARTINE";
    const kitas = KITAS_TIPAS[dabar];
    const nauji = { ...tipai };
    if (kitas === "STANDARTINE") delete nauji[r];
    else nauji[r] = kitas;
    setTipai(nauji);
  };

  const pateikti = async (ev) => {
    ev.preventDefault();
    const k = {};
    if (!pavadinimas.trim()) k.pavadinimas = "Įveskite salės pavadinimą.";
    if (!(Number(eiliu) >= 1 && Number(eiliu) <= 30)) k.eiliu = "Eilių skaičius turi būti nuo 1 iki 30.";
    if (!(Number(vietu) >= 1 && Number(vietu) <= 40)) k.vietu = "Vietų skaičius turi būti nuo 1 iki 40.";
    setKlaidos(k);
    if (Object.keys(k).length) return;

    const vietos = Object.entries(tipai)
      .map(([r, tipas]) => {
        const [ee, vv] = r.split("-").map(Number);
        return { eile: ee, vieta: vv, tipas };
      })
      .filter((x) => x.eile <= e && x.vieta <= v);
    setSiunciama(true);
    try {
      const rez = await api(pradine ? `/sales/${pradine.id}` : "/sales", {
        metodas: pradine ? "PUT" : "POST",
        kunas: { pavadinimas, eiliu: Number(eiliu), vietu: Number(vietu), vietos },
      });
      issaugota(rez);
    } catch (err) {
      const is = {};
      for (const [l, z] of Object.entries(err.duomenys || {})) is[l] = Array.isArray(z) ? z[0] : z;
      setKlaidos(Object.keys(is).length ? is : { bendra: "Nepavyko išsaugoti salės." });
    } finally {
      setSiunciama(false);
    }
  };

  const kl = (l) => `laukas${klaidos[l] ? " klaidingas" : ""}`;
  const Klaida = ({ l }) => (klaidos[l] ? <span className="lauko-klaida" role="alert">{klaidos[l]}</span> : null);

  return (
    <form className="kortele forma" onSubmit={pateikti} noValidate>
      <h2 style={{ marginTop: 0 }}>{pradine ? `Redaguoti: ${pradine.pavadinimas}` : "Nauja salė"}</h2>
      {uzrakinta && (
        <div className="pranesimas info">
          Salėje suplanuota būsimų seansų, todėl eilių ir vietų skaičiaus keisti negalima. Vietų tipus keisti galima.
        </div>
      )}
      <div className="eilute">
        <div className={kl("pavadinimas")}>
          <label htmlFor="sa-pav">Pavadinimas *</label>
          <input id="sa-pav" maxLength={50} value={pavadinimas} onChange={(x) => setPavadinimas(x.target.value)} />
          <Klaida l="pavadinimas" />
        </div>
        <div className={kl("eiliu")}>
          <label htmlFor="sa-eil">Eilių skaičius (1–30) *</label>
          <input id="sa-eil" type="number" min={1} max={30} value={eiliu} disabled={uzrakinta} onChange={(x) => setEiliu(x.target.value)} />
          <Klaida l="eiliu" />
        </div>
        <div className={kl("vietu")}>
          <label htmlFor="sa-viet">Vietų eilėje (1–40) *</label>
          <input id="sa-viet" type="number" min={1} max={40} value={vietu} disabled={uzrakinta} onChange={(x) => setVietu(x.target.value)} />
          <Klaida l="vietu" />
        </div>
      </div>
      <p className="pagalba">Spustelėkite vietą, kad pakeistumėte jos tipą: standartinė → neįgaliesiems → neprieinama.</p>
      <SalesSchema eiles={eiles} onVieta={keistiVieta} redagavimas />
      <p>Talpa: <strong>{vietuTekstas(talpa)}</strong> (iš viso {e * v}, neprieinamų {neprieinamu})</p>
      {klaidos.bendra && <div className="pranesimas klaida" role="alert">{klaidos.bendra}</div>}
      <div className="veiksmai">
        <button className="mygtukas" disabled={siunciama}>Išsaugoti</button>
        <button type="button" className="mygtukas antrinis" onClick={atsaukti}>Atšaukti</button>
      </div>
    </form>
  );
}

export default function Sales() {
  const [sales, setSales] = useState([]);
  const [redaguojama, setRedaguojama] = useState(undefined); // undefined uždaryta, null nauja
  const [pranesimas, setPranesimas] = useState(null);
  const uzdaryti = useCallback(() => setPranesimas(null), []);

  const ikelti = () => api("/sales").then(setSales);
  useEffect(() => { ikelti(); }, []);

  const atidaryti = async (id) => {
    setPranesimas(null);
    setRedaguojama(await api(`/sales/${id}`));
  };

  const issaugota = (s) => {
    setRedaguojama(undefined);
    setPranesimas({ tipas: "sekme", tekstas: `Salė „${s.pavadinimas}“ išsaugota. Talpa: ${vietuTekstas(s.talpa)}.` });
    ikelti();
  };

  return (
    <>
      <div className="eilute" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0 }}>Salės</h1>
        {redaguojama === undefined && <button className="mygtukas" onClick={() => setRedaguojama(null)}>+ Nauja salė</button>}
      </div>
      <div style={{ height: "0.75rem" }} />
      <Pranesimas pranesimas={pranesimas} uzdaryti={uzdaryti} />
      {redaguojama !== undefined && (
        <SalesRedaktorius key={redaguojama?.id ?? "nauja"} pradine={redaguojama} issaugota={issaugota}
          atsaukti={() => setRedaguojama(undefined)} />
      )}
      <div className="kortele lenteles-apvalkalas">
        <table className="lentele">
          <thead><tr><th>Salė</th><th>Talpa</th><th>Veiksmai</th></tr></thead>
          <tbody>
            {sales.map((s) => (
              <tr key={s.id}>
                <td><strong>{s.pavadinimas}</strong></td>
                <td>{vietuTekstas(s.talpa)}</td>
                <td><button className="mygtukas antrinis" onClick={() => atidaryti(s.id)}>Redaguoti schemą</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
