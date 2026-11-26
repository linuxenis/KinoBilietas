"""K6 Salių komponentas: salės schemos generavimas ir keitimas (FR-09, SAL-03, SAL-04)."""
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Eile, KinoTeatras, Sale, Vieta

NEPRIEINAMA = "NEPRIEINAMA"


class VietosTipasSerializer(serializers.Serializer):
    eile = serializers.IntegerField(min_value=1)
    vieta = serializers.IntegerField(min_value=1)
    tipas = serializers.ChoiceField(choices=["STANDARTINE", "NEIGALIESIEMS", NEPRIEINAMA])


class SalesFormaSerializer(serializers.Serializer):
    pavadinimas = serializers.CharField(max_length=50, error_messages={
        "blank": "Įveskite salės pavadinimą.", "required": "Įveskite salės pavadinimą.",
        "max_length": "Pavadinimas negali būti ilgesnis nei 50 simbolių.",
    })
    eiliu = serializers.IntegerField(min_value=1, max_value=30, error_messages={
        "required": "Įveskite eilių skaičių.", "invalid": "Eilių skaičius turi būti nuo 1 iki 30.",
        "min_value": "Eilių skaičius turi būti nuo 1 iki 30.", "max_value": "Eilių skaičius turi būti nuo 1 iki 30.",
    })
    vietu = serializers.IntegerField(min_value=1, max_value=40, error_messages={
        "required": "Įveskite vietų skaičių eilėje.", "invalid": "Vietų skaičius turi būti nuo 1 iki 40.",
        "min_value": "Vietų skaičius turi būti nuo 1 iki 40.", "max_value": "Vietų skaičius turi būti nuo 1 iki 40.",
    })
    vietos = VietosTipasSerializer(many=True, required=False)

    def validate(self, d):
        for v in d.get("vietos", []):
            if v["eile"] > d["eiliu"] or v["vieta"] > d["vietu"]:
                raise serializers.ValidationError({"vietos": "Nurodyta vieta nepatenka į salės schemą."})
        return d


class SalesKlaida(Exception):
    def __init__(self, zinute):
        super().__init__(zinute)
        self.zinute = zinute


def matmenys(sale):
    eiles = list(sale.eiles.all())
    return len(eiles), max((e.vietos.count() for e in eiles), default=0)


def turi_busimu_seansu(sale):
    from repertuaras.models import Seansas

    return Seansas.objects.filter(
        sale=sale, busena=Seansas.Busena.SUPLANUOTAS, pradzia__gt=timezone.now()
    ).exists()


def _tipai(d):
    return {(v["eile"], v["vieta"]): v["tipas"] for v in d.get("vietos", [])}


def _generuoti(sale, d):
    """SAL-03: sugeneruoja eiles ir vietas pagal eilių ir vietų skaičių."""
    tipai = _tipai(d)
    for e in range(1, d["eiliu"] + 1):
        eile = Eile.objects.create(sale=sale, numeris=e)
        Vieta.objects.bulk_create([
            Vieta(
                eile=eile, numeris=v,
                tipas="NEIGALIESIEMS" if tipai.get((e, v)) == "NEIGALIESIEMS" else "STANDARTINE",
                prieinama=tipai.get((e, v)) != NEPRIEINAMA,
            )
            for v in range(1, d["vietu"] + 1)
        ])


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
        tipai = _tipai(d)
        for v in Vieta.objects.filter(eile__sale=sale).select_related("eile"):
            tipas = tipai.get((v.eile.numeris, v.numeris), "STANDARTINE")
            v.tipas = "NEIGALIESIEMS" if tipas == "NEIGALIESIEMS" else "STANDARTINE"
            v.prieinama = tipas != NEPRIEINAMA
            v.save(update_fields=["tipas", "prieinama"])
    sale.pavadinimas = d["pavadinimas"]
    sale.save(update_fields=["pavadinimas"])
    return sale
