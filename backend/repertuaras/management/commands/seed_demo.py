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
F3D_PRIEDAS = Decimal("2.00")
SEANSU_DIENOS = 14
PIRMO_SEANSO_VALANDA = 11  # kiekviena kita salė pradeda viena valanda vėliau
PASKUTINIO_SEANSO_PRADZIA = 22  # naujų seansų po šios valandos nebepradedama
N18_PRADZIA = 20  # N-18 filmas rodomas tik vakare
SEANSU_TARPAS_MIN = 15  # kito seanso pradžia suapvalinama iki 15 min.
DEMO_ADMIN_EL_PASTAS = "admin@kinobilietas.lt"
DEMO_KLIENTAI = [("Ona", "ona@pavyzdys.lt"), ("Jonas", "jonas@pavyzdys.lt"), ("Eglė", "egle@pavyzdys.lt")]


def _per_anksti(filmas, pradzia):
    return filmas.cenzas == Filmas.Cenzas.N18 and pradzia.hour < N18_PRADZIA


def _formatas(yra_pirma_sale, filmas):
    yra_duna = filmas.pavadinimas.startswith("Dūna")
    return Seansas.Formatas.F3D if yra_pirma_sale and yra_duna else Seansas.Formatas.F2D


def _kito_seanso_pradzia(pabaiga):
    papildymas = timedelta(minutes=(SEANSU_TARPAS_MIN - pabaiga.minute % SEANSU_TARPAS_MIN) % SEANSU_TARPAS_MIN)
    return (pabaiga + papildymas).replace(second=0, microsecond=0)


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
            self._isvalyti()

        sales = self._sukurti_sales()
        filmai, zanrai = self._sukurti_filmus()
        seansu_kiekis = self._sukurti_seansus(sales, filmai)
        self._sukurti_naudotojus()

        self.stdout.write(self.style.SUCCESS(
            f"Sukurta: 3 salės, {len(filmai)} filmai, {len(zanrai)} žanrai, {seansu_kiekis} seansai, 4 naudotojai."
        ))

    def _isvalyti(self):
        SeansoKaina.objects.all().delete()
        Seansas.objects.all().delete()
        for f in Filmas.objects.exclude(plakatas=""):
            f.plakatas.delete(save=False)
        Filmas.objects.all().delete()
        FilmuPlatintojas.objects.all().delete()
        Zanras.objects.all().delete()
        KinoTeatras.objects.all().delete()
        Naudotojas.objects.filter(is_superuser=False).delete()

    def _sukurti_sales(self):
        teatras = KinoTeatras.objects.create(
            pavadinimas=settings.KINO_TEATRAS["pavadinimas"], adresas=settings.KINO_TEATRAS["adresas"],
            telefonas="+370 600 00000", el_pastas="info@kinobilietas.lt",
        )
        return [
            self._sale(teatras, "1 salė", eiliu=8, vietu=15, neigaliesiems=[(1, 1), (1, 2)], neprieinamos=[(8, 15)]),
            self._sale(teatras, "2 salė", eiliu=6, vietu=12, neigaliesiems=[(1, 1)], neprieinamos=[]),
            self._sale(teatras, "VIP salė", eiliu=4, vietu=8, neigaliesiems=[], neprieinamos=[]),
        ]

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

    def _sukurti_filmus(self):
        platintojai = [FilmuPlatintojas.objects.create(pavadinimas=p, el_pastas=e) for p, e in PLATINTOJAI]
        zanrai = {}
        filmai = [self._sukurti_filma(d, platintojai[d["platintojas"]], zanrai) for d in FILMAI]
        return filmai, zanrai

    def _sukurti_filma(self, d, platintojas, zanrai):
        """Sukuria filmą su plakatu ir žanrais; naujus žanrus įrašo į žodyną zanrai."""
        filmas = Filmas.objects.create(
            pavadinimas=d["pavadinimas"], originalus_pavadinimas=d["originalus_pavadinimas"],
            aprasymas=d["aprasymas"], trukme_min=d["trukme_min"], cenzas=d["cenzas"],
            kalba=d["kalba"], premjeros_data=d["premjera"], platintojas=platintojas,
        )
        plakatas = PLAKATAI / d["plakatas"]
        if plakatas.exists():
            with plakatas.open("rb") as failas:
                filmas.plakatas.save(d["plakatas"], File(failas), save=True)
        for pavadinimas in d["zanrai"]:
            if pavadinimas not in zanrai:
                zanrai[pavadinimas] = Zanras.objects.create(pavadinimas=pavadinimas)
            filmas.zanrai.add(zanrai[pavadinimas])
        return filmas

    def _sukurti_seansus(self, sales, filmai):
        """Seansai 14 dienų: kiekvienoje salėje filmai iš eilės, be persidengimų."""
        siandien = timezone.localdate()
        kiekis = 0
        for diena in range(SEANSU_DIENOS):
            data = siandien + timedelta(days=diena)
            for sale_nr, sale in enumerate(sales):
                kiekis += self._sukurti_dienos_seansus(sale, sale_nr, data, diena, filmai)
        return kiekis

    def _sukurti_dienos_seansus(self, sale, sale_nr, data, diena, filmai):
        """Vienos salės vienos dienos seansai iš eilės. Grąžina sukurtų seansų skaičių."""
        tz = timezone.get_current_timezone()
        pradzia = datetime.combine(data, time(PIRMO_SEANSO_VALANDA + sale_nr, 0), tzinfo=tz)
        filmo_nr = (diena + sale_nr * 2) % len(filmai)
        kiekis = 0
        while pradzia.hour < PASKUTINIO_SEANSO_PRADZIA and pradzia.date() == data:
            filmas = filmai[filmo_nr % len(filmai)]
            filmo_nr += 1
            if _per_anksti(filmas, pradzia):
                continue
            seansas = self._sukurti_seansa(sale, filmas, pradzia, yra_pirma_sale=sale_nr == 0)
            kiekis += 1
            pradzia = _kito_seanso_pradzia(seansas.pabaiga)
        return kiekis

    def _sukurti_seansa(self, sale, filmas, pradzia, yra_pirma_sale):
        formatas = _formatas(yra_pirma_sale, filmas)
        seansas = Seansas.objects.create(
            filmas=filmas, sale=sale, pradzia=pradzia, formatas=formatas,
            pabaiga=Seansas.apskaiciuoti_pabaiga(pradzia, filmas.trukme_min),
        )
        priedas = F3D_PRIEDAS if formatas == Seansas.Formatas.F3D else Decimal("0")
        for tipas, suma in KAINOS.items():
            SeansoKaina.objects.create(seansas=seansas, bilieto_tipas=tipas, suma=suma + priedas)
        return seansas

    def _sukurti_naudotojus(self):
        admin_slaptazodis = os.environ.get("DEMO_ADMIN_PASSWORD", "Admin2026")
        kliento_slaptazodis = os.environ.get("DEMO_KLIENTO_SLAPTAZODIS", "Kinas2026")
        if not Naudotojas.objects.filter(email=DEMO_ADMIN_EL_PASTAS).exists():
            Naudotojas.objects.create_user(
                email=DEMO_ADMIN_EL_PASTAS, password=admin_slaptazodis, vardas="Administratorius",
                role=Naudotojas.Role.ADMINISTRATORIUS, is_staff=True,
            )
        for vardas, email in DEMO_KLIENTAI:
            Naudotojas.objects.create_user(
                email=email, password=kliento_slaptazodis, vardas=vardas,
                sutikimas_su_politika=True, sutikimo_data=timezone.now(),
            )
