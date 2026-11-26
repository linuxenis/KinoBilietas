"""Demonstracinių duomenų rinkinys (NFR-08): 2 salės, 6 filmai, seansai 14 d.

Paleidimas: python manage.py seed_demo [--is-naujo]
Seansai kuriami nuo šiandienos, todėl demonstracija veikia bet kurią dieną.
"""
import os
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from naudotojai.models import Naudotojas
from repertuaras.models import Filmas, FilmuPlatintojas, Seansas, SeansoKaina, Zanras
from sales.models import Eile, KinoTeatras, Sale, Vieta

FILMAI = [
    {
        "pavadinimas": "Dūna: antroji dalis", "plakatas": "duna.jpg", "originalus_pavadinimas": "Dune: Part Two",
        "trukme_min": 166, "cenzas": "N13", "zanrai": ["Fantastika", "Nuotykių"],
        "kalba": "Anglų k., lietuviški subtitrai", "premjera": "2024-03-01", "platintojas": 0,
        "aprasymas": "Paulius Atreidas susivienija su fremenais ir keršija sąmokslininkams, "
                     "sunaikinusiems jo šeimą. Jis turi rinktis tarp meilės ir visatos likimo.",
    },
    {
        "pavadinimas": "Išvirkščias pasaulis 2", "plakatas": "isvirksciaspasaulis2.jpg", "originalus_pavadinimas": "Inside Out 2",
        "trukme_min": 96, "cenzas": "V", "zanrai": ["Animacija", "Komedija"],
        "kalba": "Dubliuotas lietuviškai", "premjera": "2024-06-14", "platintojas": 1,
        "aprasymas": "Paauglystės sulaukusios Railės galvoje atsiranda naujos emocijos, "
                     "o Džiaugsmas su draugais turi išmokti su jomis sutarti.",
    },
    {
        "pavadinimas": "Laukinis robotas", "plakatas": "laukinisrobotas.jpg", "originalus_pavadinimas": "The Wild Robot",
        "trukme_min": 102, "cenzas": "V", "zanrai": ["Animacija", "Nuotykių"],
        "kalba": "Dubliuotas lietuviškai", "premjera": "2024-10-11", "platintojas": 2,
        "aprasymas": "Robotė Roz po audros atsiduria negyvenamoje saloje ir mokosi išgyventi "
                     "laukinėje gamtoje, globodama našlaitį žąsiuką.",
    },
    {
        "pavadinimas": "Oppenheimeris", "plakatas": "oppenheimeris.jpg", "originalus_pavadinimas": "Oppenheimer",
        "trukme_min": 180, "cenzas": "N16", "zanrai": ["Drama", "Biografinis"],
        "kalba": "Anglų k., lietuviški subtitrai", "premjera": "2023-07-21", "platintojas": 2,
        "aprasymas": "Fiziko J. Roberto Oppenheimerio istorija: Manhatano projektas ir "
                     "pirmosios atominės bombos sukūrimo kaina.",
    },
    {
        "pavadinimas": "Gladiatorius II", "plakatas": "gladiatorius2.jpg", "originalus_pavadinimas": "Gladiator II",
        "trukme_min": 148, "cenzas": "N16", "zanrai": ["Veiksmo", "Drama"],
        "kalba": "Anglų k., lietuviški subtitrai", "premjera": "2024-11-15", "platintojas": 1,
        "aprasymas": "Lukijus, praradęs namus, tampa gladiatoriumi ir kovoja Koliziejuje, "
                     "kad grąžintų Romai jos šlovę.",
    },
    {
        "pavadinimas": "Kalbėk su manimi", "plakatas": "kalbeksumanimi.jpg", "originalus_pavadinimas": "Talk to Me",
        "trukme_min": 95, "cenzas": "N18", "zanrai": ["Siaubo"],
        "kalba": "Anglų k., lietuviški subtitrai", "premjera": "2023-07-28", "platintojas": 0,
        "aprasymas": "Draugų kompanija atranda būdą iškviesti dvasias balzamuota ranka, "
                     "kol vienas iš jų nueina per toli.",
    },
]

PLATINTOJAI = [
    ("Acme Film", "info@acmefilm.lt"),
    ("Theatrical Distribution", "info@theatrical.lt"),
    ("ACME Baltic", "baltic@acme.lt"),
]

# Plakatai: oficialūs filmų plakatai mažos raiškos (Wikipedia), tik mokomajai demonstracijai
PLAKATAI = Path(__file__).resolve().parents[2] / "demo_plakatai"

KAINOS = {"SUAUGUSIOJO": Decimal("6.50"), "STUDENTO": Decimal("5.00"), "SENJORO": Decimal("4.50")}


class Command(BaseCommand):
    help = "Sukuria demonstracinius duomenis (NFR-08)."

    def add_arguments(self, parser):
        parser.add_argument("--is-naujo", action="store_true", help="Ištrinti esamus duomenis ir sukurti iš naujo.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if Filmas.objects.exists() and not opts["is_naujo"]:
            self.stdout.write("Demonstraciniai duomenys jau yra, praleidžiama.")
            return
        if opts["is_naujo"]:
            SeansoKaina.objects.all().delete()
            Seansas.objects.all().delete()
            for f in Filmas.objects.exclude(plakatas=""):
                f.plakatas.delete(save=False)
            Filmas.objects.all().delete()
            FilmuPlatintojas.objects.all().delete()
            Zanras.objects.all().delete()
            KinoTeatras.objects.all().delete()
            Naudotojas.objects.filter(is_superuser=False).delete()

        teatras = KinoTeatras.objects.create(
            pavadinimas=settings.KINO_TEATRAS["pavadinimas"], adresas=settings.KINO_TEATRAS["adresas"],
            telefonas="+370 600 00000", el_pastas="info@kinobilietas.lt",
        )
        sale1 = self._sale(teatras, "1 salė", eiliu=8, vietu=15,
                           neigaliesiems=[(1, 1), (1, 2)], neprieinamos=[(8, 15)])
        sale2 = self._sale(teatras, "2 salė", eiliu=6, vietu=12,
                           neigaliesiems=[(1, 1)], neprieinamos=[])
        sale3 = self._sale(teatras, "VIP salė", eiliu=4, vietu=8, neigaliesiems=[], neprieinamos=[])

        platintojai = [FilmuPlatintojas.objects.create(pavadinimas=p, el_pastas=e) for p, e in PLATINTOJAI]
        zanrai = {}
        filmai = []
        for d in FILMAI:
            f = Filmas.objects.create(
                pavadinimas=d["pavadinimas"], originalus_pavadinimas=d["originalus_pavadinimas"],
                aprasymas=d["aprasymas"], trukme_min=d["trukme_min"], cenzas=d["cenzas"],
                kalba=d["kalba"], premjeros_data=d["premjera"], platintojas=platintojai[d["platintojas"]],
            )
            plakatas = PLAKATAI / d["plakatas"]
            if plakatas.exists():
                with plakatas.open("rb") as failas:
                    f.plakatas.save(d["plakatas"], File(failas), save=True)
            for z in d["zanrai"]:
                if z not in zanrai:
                    zanrai[z] = Zanras.objects.create(pavadinimas=z)
                f.zanrai.add(zanrai[z])
            filmai.append(f)

        # Seansai 14 dienų: kiekvienoje salėje filmai iš eilės, be persidengimų
        tz = timezone.get_current_timezone()
        siandien = timezone.localdate()
        kiekis = 0
        for diena in range(14):
            data = siandien + timedelta(days=diena)
            for s_idx, sale in enumerate([sale1, sale2, sale3]):
                pradzia = datetime.combine(data, time(11 + s_idx, 0), tzinfo=tz)
                f_idx = (diena + s_idx * 2) % len(filmai)
                while pradzia.hour < 22 and pradzia.date() == data:
                    filmas = filmai[f_idx % len(filmai)]
                    # N-18 filmas rodomas tik vakare
                    if filmas.cenzas == "N18" and pradzia.hour < 20:
                        f_idx += 1
                        continue
                    pabaiga = Seansas.apskaiciuoti_pabaiga(pradzia, filmas.trukme_min)
                    formatas = "F3D" if (sale is sale1 and filmas.pavadinimas.startswith("Dūna")) else "F2D"
                    seansas = Seansas.objects.create(
                        filmas=filmas, sale=sale, pradzia=pradzia, pabaiga=pabaiga, formatas=formatas,
                    )
                    priedas = Decimal("2.00") if formatas == "F3D" else Decimal("0")
                    for tipas, suma in KAINOS.items():
                        SeansoKaina.objects.create(seansas=seansas, bilieto_tipas=tipas, suma=suma + priedas)
                    kiekis += 1
                    # Kitas seansas: po pabaigos, suapvalinus iki 15 min.
                    kitas = pabaiga + timedelta(minutes=(15 - pabaiga.minute % 15) % 15)
                    pradzia = kitas.replace(second=0, microsecond=0)
                    f_idx += 1

        admin_slaptazodis = os.environ.get("DEMO_ADMIN_PASSWORD", "Admin2026")
        if not Naudotojas.objects.filter(email="admin@kinobilietas.lt").exists():
            Naudotojas.objects.create_user(
                email="admin@kinobilietas.lt", password=admin_slaptazodis, vardas="Administratorius",
                role=Naudotojas.Role.ADMINISTRATORIUS, is_staff=True,
            )
        for vardas, email in [("Ona", "ona@pavyzdys.lt"), ("Jonas", "jonas@pavyzdys.lt"), ("Eglė", "egle@pavyzdys.lt")]:
            Naudotojas.objects.create_user(
                email=email, password="Kinas2026", vardas=vardas,
                sutikimas_su_politika=True, sutikimo_data=timezone.now(),
            )

        self.stdout.write(self.style.SUCCESS(
            f"Sukurta: 3 salės, {len(filmai)} filmai, {len(zanrai)} žanrai, {kiekis} seansai, 4 naudotojai."
        ))

    def _sale(self, teatras, pavadinimas, eiliu, vietu, neigaliesiems, neprieinamos):
        sale = Sale.objects.create(kino_teatras=teatras, pavadinimas=pavadinimas)
        for e in range(1, eiliu + 1):
            eile = Eile.objects.create(sale=sale, numeris=e)
            Vieta.objects.bulk_create([
                Vieta(
                    eile=eile, numeris=v,
                    tipas=Vieta.Tipas.NEIGALIESIEMS if (e, v) in neigaliesiems else Vieta.Tipas.STANDARTINE,
                    prieinama=(e, v) not in neprieinamos,
                )
                for v in range(1, vietu + 1)
            ])
        return sale
