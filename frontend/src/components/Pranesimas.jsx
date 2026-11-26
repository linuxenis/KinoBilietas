// Patvirtinimai rodomi lango viršuje ir išnyksta po 5 s (2.4.1 pranešimų reikalavimai)
import { useEffect } from "react";

export default function Pranesimas({ pranesimas, uzdaryti }) {
  useEffect(() => {
    if (!pranesimas || pranesimas.tipas !== "sekme") return undefined;
    const t = setTimeout(uzdaryti, 5000);
    return () => clearTimeout(t);
  }, [pranesimas, uzdaryti]);

  if (!pranesimas) return null;
  return (
    <div className={`pranesimas ${pranesimas.tipas}`} role={pranesimas.tipas === "klaida" ? "alert" : "status"}>
      {pranesimas.tekstas}
    </div>
  );
}
