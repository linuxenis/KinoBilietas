// REST API klientas (NFR-03: JSON, adresai /api/v1/)
const BAZE = "/api/v1";
export const SESIJA_BAIGESI = "kinobilietas:sesija-baigesi";

export function gautiZetona() {
  try {
    return localStorage.getItem("prieigos_zetonas");
  } catch {
    return null;
  }
}

// Pasibaigusi ar nebegaliojanti sesija išvaloma, o sąsaja apie tai informuojama
export function isvalytiSesija() {
  try {
    localStorage.removeItem("prieigos_zetonas");
    localStorage.removeItem("atnaujinimo_zetonas");
    localStorage.removeItem("naudotojas");
  } catch {
    /* nesaugoma */
  }
  window.dispatchEvent(new Event(SESIJA_BAIGESI));
}

export class ApiKlaida extends Error {
  constructor(statusas, duomenys) {
    super((duomenys && (duomenys.detail || duomenys.klaida)) || `Klaida ${statusas}`);
    this.statusas = statusas;
    this.duomenys = duomenys || {};
  }
}

export async function api(kelias, { metodas = "GET", kunas } = {}, kartojama = false) {
  const antrastes = { Accept: "application/json" };
  const zetonas = kartojama ? null : gautiZetona();
  if (zetonas) antrastes.Authorization = `Bearer ${zetonas}`;
  const failai = typeof FormData !== "undefined" && kunas instanceof FormData;
  if (kunas !== undefined && !failai) antrastes["Content-Type"] = "application/json";

  const atsakas = await fetch(BAZE + kelias, {
    method: metodas,
    headers: antrastes,
    body: kunas === undefined ? undefined : failai ? kunas : JSON.stringify(kunas),
  });
  const tekstas = await atsakas.text();
  let duomenys = null;
  try {
    duomenys = tekstas ? JSON.parse(tekstas) : null;
  } catch {
    duomenys = null;
  }

  // Nebegaliojantis žetonas: sesija išvaloma, užklausa kartojama kaip neregistruoto žiūrovo
  if (atsakas.status === 401 && zetonas) {
    isvalytiSesija();
    return api(kelias, { metodas, kunas }, true);
  }
  if (!atsakas.ok) throw new ApiKlaida(atsakas.status, duomenys);
  return duomenys;
}
