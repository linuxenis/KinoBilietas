// NFR-05: kainos „7,50 €“, datos MMMM-MM-DD, laikas VV:MM Europe/Vilnius
const LAIKO_JUOSTA = "Europe/Vilnius";

export function kaina(suma) {
  return `${Number(suma).toFixed(2).replace(".", ",")} €`;
}

export function data(iso) {
  return new Intl.DateTimeFormat("sv-SE", { timeZone: LAIKO_JUOSTA }).format(new Date(iso));
}

export function laikas(iso) {
  return new Intl.DateTimeFormat("lt-LT", {
    timeZone: LAIKO_JUOSTA, hour: "2-digit", minute: "2-digit", hour12: false,
  }).format(new Date(iso));
}

export function siandien() {
  return data(new Date().toISOString());
}

export function pridetiDienu(dataTekstas, dienos) {
  const d = new Date(`${dataTekstas}T12:00:00`);
  d.setDate(d.getDate() + dienos);
  return data(d.toISOString());
}

const SAVAITES_DIENOS = ["Sk", "Pr", "An", "Tr", "Kt", "Pn", "Št"];
export function savaitesDiena(dataTekstas) {
  return SAVAITES_DIENOS[new Date(`${dataTekstas}T12:00:00`).getDay()];
}

export const CENZAI = { V: "V", N7: "N-7", N13: "N-13", N16: "N-16", N18: "N-18" };
export const FORMATAI = { F2D: "2D", F3D: "3D" };

// Lietuviškos daugiskaitos formos: 1 vieta, 2 vietos, 10 vietų, 21 vieta
export function vietos(n) {
  const v = n % 10, s = n % 100;
  if (v === 1 && s !== 11) return `${n} vieta`;
  if (v >= 2 && (s < 10 || s >= 20)) return `${n} vietos`;
  return `${n} vietų`;
}
