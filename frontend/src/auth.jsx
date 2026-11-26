// K1/K4: prisijungusio naudotojo būsena žiūrovų ir administravimo sąsajoms
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, SESIJA_BAIGESI } from "./api.js";

const AuthKontekstas = createContext(null);

function saugoti(raktas, reiksme) {
  try {
    if (reiksme === null) localStorage.removeItem(raktas);
    else localStorage.setItem(raktas, reiksme);
  } catch {
    /* naršyklė neleidžia saugoti: sesija galios tik iki puslapio perkrovimo */
  }
}

function skaityti(raktas) {
  try {
    return localStorage.getItem(raktas);
  } catch {
    return null;
  }
}

export function AuthTiekejas({ children }) {
  const [naudotojas, setNaudotojas] = useState(() => {
    const t = skaityti("naudotojas");
    return t ? JSON.parse(t) : null;
  });

  const issaugotiSesija = useCallback((atsakas) => {
    saugoti("prieigos_zetonas", atsakas.prieigos);
    saugoti("atnaujinimo_zetonas", atsakas.atnaujinimo);
    saugoti("naudotojas", JSON.stringify(atsakas.naudotojas));
    setNaudotojas(atsakas.naudotojas);
    return atsakas.naudotojas;
  }, []);

  const isvalyti = useCallback(() => {
    saugoti("prieigos_zetonas", null);
    saugoti("atnaujinimo_zetonas", null);
    saugoti("naudotojas", null);
    setNaudotojas(null);
  }, []);

  // Patikrinama, ar išsaugota sesija dar galioja
  useEffect(() => {
    if (!skaityti("prieigos_zetonas")) return;
    api("/auth/as").catch(() => isvalyti());
  }, [isvalyti]);

  // API klientas praneša, kai žetonas nebegalioja (pvz. paskyra pašalinta ar pasibaigė galiojimas)
  useEffect(() => {
    const baigti = () => setNaudotojas(null);
    window.addEventListener(SESIJA_BAIGESI, baigti);
    return () => window.removeEventListener(SESIJA_BAIGESI, baigti);
  }, []);

  const prisijungti = (email, slaptazodis) =>
    api("/auth/prisijungimas", { metodas: "POST", kunas: { email, slaptazodis } }).then(issaugotiSesija);

  const registruotis = (duomenys) =>
    api("/auth/registracija", { metodas: "POST", kunas: duomenys }).then(issaugotiSesija);

  const atsijungti = async () => {
    try {
      await api("/auth/atsijungimas", { metodas: "POST", kunas: { atnaujinimo: skaityti("atnaujinimo_zetonas") } });
    } catch {
      /* sesija jau negalioja */
    }
    isvalyti();
  };

  const yraAdmin = naudotojas?.role === "ADMINISTRATORIUS";

  return (
    <AuthKontekstas.Provider value={{ naudotojas, yraAdmin, prisijungti, registruotis, atsijungti }}>
      {children}
    </AuthKontekstas.Provider>
  );
}

export function useAuth() {
  return useContext(AuthKontekstas);
}
