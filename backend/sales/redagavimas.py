"""K6 Salių komponentas: salės schemos generavimas ir keitimas (FR-09, SAL-03, SAL-04)."""
from django.db import transaction
from django.utils import timezone

from .models import NEPRIEINAMA, Eile, KinoTeatras, Sale, Vieta


class SalesKlaida(Exception):
    def __init__(self, zinute):
        super().__init__(zinute)
        self.zinute = zinute


def matmenys(sale):
    eiles = list(sale.eiles.all())
    return len(eiles), max((e.vietos.count() for e in eiles), default=0)


def turi_busimu_seansu(sale):
    """Naudoja atvirkštinį ryšį sale.seansai, todėl salių komponentui nereikia importuoti repertuaro."""
    seansai = sale.seansai
    return seansai.filter(busena=seansai.model.Busena.SUPLANUOTAS, pradzia__gt=timezone.now()).exists()


def _tipai(d):
    return {(v["eile"], v["vieta"]): v["tipas"] for v in d.get("vietos", [])}


def _vietos_savybes(tipas_formoje):
    """Formos tipą (STANDARTINE / NEIGALIESIEMS / NEPRIEINAMA) paverčia modelio laukais: (tipas, prieinama)."""
    tipas = Vieta.Tipas.NEIGALIESIEMS if tipas_formoje == Vieta.Tipas.NEIGALIESIEMS else Vieta.Tipas.STANDARTINE
    return tipas, tipas_formoje != NEPRIEINAMA


def _generuoti(sale, d):
    """SAL-03: sugeneruoja eiles ir vietas pagal eilių ir vietų skaičių."""
    tipai = _tipai(d)
    for e in range(1, d["eiliu"] + 1):
        eile = Eile.objects.create(sale=sale, numeris=e)
        vietos = []
        for v in range(1, d["vietu"] + 1):
            tipas, prieinama = _vietos_savybes(tipai.get((e, v), Vieta.Tipas.STANDARTINE))
            vietos.append(Vieta(eile=eile, numeris=v, tipas=tipas, prieinama=prieinama))
        Vieta.objects.bulk_create(vietos)


def _atnaujinti_vietu_tipus(sale, d):
    """Pakeičia tik vietų tipus ir prieinamumą (viena bulk_update užklausa vietoj užklausos kiekvienai vietai)."""
    tipai = _tipai(d)
    vietos = list(Vieta.objects.filter(eile__sale=sale).select_related("eile"))
    for v in vietos:
        v.tipas, v.prieinama = _vietos_savybes(tipai.get((v.eile.numeris, v.numeris), Vieta.Tipas.STANDARTINE))
    Vieta.objects.bulk_update(vietos, ["tipas", "prieinama"])


@transaction.atomic
def sukurti(d):
    teatras = KinoTeatras.objects.first() or KinoTeatras.objects.create(pavadinimas="Kino teatras")
    sale = Sale.objects.create(kino_teatras=teatras, pavadinimas=d["pavadinimas"])
    _generuoti(sale, d)
    return sale


@transaction.atomic
def atnaujinti(sale, d):
    """Vietų tipus keisti galima visada; eilių ir vietų skaičių tik jei nėra būsimų seansų (SAL-04)."""
    sale = Sale.objects.select_for_update().get(pk=sale.pk)
    if (d["eiliu"], d["vietu"]) != matmenys(sale):
        if turi_busimu_seansu(sale):
            raise SalesKlaida(
                f"Salės „{sale.pavadinimas}“ eilių ir vietų skaičiaus keisti negalima: "
                "joje suplanuota būsimų seansų."
            )
        sale.eiles.all().delete()
        _generuoti(sale, d)
    else:
        _atnaujinti_vietu_tipus(sale, d)
    sale.pavadinimas = d["pavadinimas"]
    sale.save(update_fields=["pavadinimas"])
    return sale
