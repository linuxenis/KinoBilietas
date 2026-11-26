// Filmo plakatas; jei paveikslo nėra, rodomas spalvotas ruošinys su pavadinimu
const SPALVOS = ["#7d1714", "#24467a", "#1f6b3a", "#6b3f8a", "#8a5a00", "#2f5f6b", "#5c3b2e"];

function spalva(tekstas) {
  let h = 0;
  for (const c of tekstas) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return SPALVOS[h % SPALVOS.length];
}

export default function Plakatas({ filmas, didelis = false }) {
  const klase = `plakatas${didelis ? " didelis" : ""}`;
  if (filmas.plakatas) {
    return <img className={klase} src={filmas.plakatas} alt={`${filmas.pavadinimas} plakatas`} />;
  }
  return (
    <div className={klase} style={{ background: spalva(filmas.pavadinimas) }} aria-hidden="true">
      {filmas.pavadinimas}
    </div>
  );
}
