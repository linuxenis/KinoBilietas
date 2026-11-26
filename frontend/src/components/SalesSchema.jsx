// NFR-10: pakartotinai panaudojamas salės schemos komponentas (2.12 pav.)
// Naudojamas žiūrovų sąsajoje vietoms rinktis ir administravimo sąsajoje salėms redaguoti.
export function vietosRaktas(eile, vieta) {
  return `${eile}-${vieta}`;
}

export default function SalesSchema({ eiles, pasirinktos = new Set(), onVieta, redagavimas = false }) {
  return (
    <div className="schema">
      <div className="ekranas" aria-hidden="true">EKRANAS</div>
      <div role="grid" aria-label="Salės schema">
        {eiles.map((eile) => (
          <div key={eile.numeris} className="schemos-eile" role="row">
            <span className="eiles-nr" aria-hidden="true">{eile.numeris}</span>
            {eile.vietos.map((v) => {
              const raktas = vietosRaktas(eile.numeris, v.numeris);
              const neprieinama = v.busena === "NEPRIEINAMA";
              const pasirinkta = pasirinktos.has(raktas);
              const klases = ["vieta"];
              if (pasirinkta) klases.push("pasirinkta");
              if (neprieinama) klases.push("neprieinama");
              if (v.tipas === "NEIGALIESIEMS") klases.push("neigaliesiems");
              return (
                <button
                  key={raktas}
                  type="button"
                  role="gridcell"
                  className={klases.join(" ")}
                  disabled={neprieinama && !redagavimas}
                  aria-pressed={pasirinkta}
                  aria-label={`${eile.numeris} eilė, ${v.numeris} vieta${neprieinama ? ", neprieinama" : ""}${v.tipas === "NEIGALIESIEMS" ? ", neįgaliesiems" : ""}`}
                  onClick={() => onVieta && onVieta(eile, v)}
                >
                  {v.numeris}
                </button>
              );
            })}
            <span className="eiles-nr" aria-hidden="true">{eile.numeris}</span>
          </div>
        ))}
      </div>
      <div className="legenda">
        <span><span className="vieta" /> Laisva</span>
        {!redagavimas && <span><span className="vieta pasirinkta" /> Pasirinkta</span>}
        <span><span className="vieta neprieinama" /> Neprieinama</span>
        <span><span className="vieta neigaliesiems" /> Neįgaliesiems</span>
      </div>
    </div>
  );
}
