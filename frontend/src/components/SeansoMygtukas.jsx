// 2-5 lentelė: seansas = mygtukas su laiku, sale, formatu, mažiausia kaina ir laisvomis vietomis
import { Link } from "react-router-dom";
import { FORMATAI, kaina, laikas, vietos } from "../formatas.js";

export default function SeansoMygtukas({ seansas }) {
  return (
    <Link className="seansas" to={`/seansai/${seansas.id}`}
      aria-label={`Seansas ${laikas(seansas.pradzia)}, ${seansas.sale}, rinktis vietas`}>
      <strong>{laikas(seansas.pradzia)}</strong>
      <small>{seansas.sale} · {FORMATAI[seansas.formatas]}</small>
      <small>nuo {kaina(seansas.maziausia_kaina)} · {vietos(seansas.laisvos_vietos)}</small>
    </Link>
  );
}
