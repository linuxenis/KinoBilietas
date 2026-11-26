"""K5 Repertuaro komponentas: seansų kūrimas, redagavimas ir atšaukimas (FR-07, FR-08).

REP-05: pabaigos skaičiavimas ir draudimas kurti seansą praeityje.
REP-06: persidengimo su kitu tos salės seansu tikrinimas.
DV-03: seansas ir jo kainos išsaugomi vienoje transakcijoje (NFR-02).
"""
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from sales.models import Sale

from .models import Seansas, SeansoKaina


class SeansoKlaida(Exception):
    def __init__(self, laukai=None, konfliktas=None, statusas=400):
        super().__init__("Seanso klaida")
        self.laukai = laukai or {}
        self.konfliktas = konfliktas
        self.statusas = statusas


def konfliktuojantis(sale, pradzia, pabaiga, isskyrus_id=None):
    """REP-06: SUPLANUOTAS tos pačios salės seansas, kurio laikas kertasi su [pradzia, pabaiga)."""
    qs = Seansas.objects.filter(
        sale=sale, busena=Seansas.Busena.SUPLANUOTAS, pradzia__lt=pabaiga, pabaiga__gt=pradzia,
    ).select_related("filmas", "sale")
    if isskyrus_id:
        qs = qs.exclude(pk=isskyrus_id)
    return qs.order_by("pradzia").first()


def konflikto_pranesimas(k):
    nuo = timezone.localtime(k.pradzia).strftime("%H:%M")
    iki = timezone.localtime(k.pabaiga).strftime("%H:%M")
    pav = k.sale.pavadinimas
    kur = pav[:-4] + "salėje" if pav.endswith("salė") else f"Salėje „{pav}“"  # „1 salė“ -> „1 salėje“
    return (
        f"{kur} tuo metu jau numatytas seansas „{k.filmas.pavadinimas}“ ({nuo}–{iki}). "
        "Pasirinkite kitą laiką arba salę."
    )


def _pradzia(data, laikas):
    return datetime.combine(data, laikas, tzinfo=timezone.get_current_timezone())


@transaction.atomic
def issaugoti_seansa(d, seansas=None):
    """Sukuria naują arba atnaujina esamą seansą. d: patikrinti formos duomenys."""
    # Salė užrakinama transakcijos metu, kad du administratoriai vienu metu nesukurtų persidengiančių seansų
    sale = Sale.objects.select_for_update().get(pk=d["sale"].pk)
    filmas = d["filmas"]
    pradzia = _pradzia(d["data"], d["pradzia"])
    pabaiga = Seansas.apskaiciuoti_pabaiga(pradzia, filmas.trukme_min)

    if pradzia <= timezone.now():
        raise SeansoKlaida({"pradzia": "Seanso praeityje sukurti negalima."})

    k = konfliktuojantis(sale, pradzia, pabaiga, isskyrus_id=seansas.pk if seansas else None)
    if k:
        raise SeansoKlaida(
            {"bendra": konflikto_pranesimas(k)},
            konfliktas={"id": k.id, "filmas": k.filmas.pavadinimas, "pradzia": k.pradzia, "pabaiga": k.pabaiga},
            statusas=409,
        )

    if seansas is None:
        seansas = Seansas(busena=Seansas.Busena.SUPLANUOTAS)
    seansas.filmas = filmas
    seansas.sale = sale
    seansas.pradzia = pradzia
    seansas.pabaiga = pabaiga
    seansas.formatas = d["formatas"]
    seansas.save()

    seansas.kainos.all().delete()
    kainos = [("SUAUGUSIOJO", d["kaina_suaugusiojo"]), ("STUDENTO", d.get("kaina_studento")),
              ("SENJORO", d.get("kaina_senjoro"))]
    SeansoKaina.objects.bulk_create([
        SeansoKaina(seansas=seansas, bilieto_tipas=tipas, suma=suma) for tipas, suma in kainos if suma is not None
    ])
    return seansas


def atsaukti(seansas):
    """REP-07: būsena ATŠAUKTAS, seansas nebematomas repertuare."""
    seansas.busena = Seansas.Busena.ATSAUKTAS
    seansas.save(update_fields=["busena"])
    return seansas
