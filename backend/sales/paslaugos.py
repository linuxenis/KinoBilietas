"""K6 Salių komponento paslaugos, kurias naudoja kiti komponentai."""
from django.db.models import Count, Q

from .models import Sale, Vieta


def prieinamu_vietu_skaicius(sale_ids):
    """SAL-01: grąžina {salės id: prieinamų vietų skaičius}.

    1 sprinte vietos neužrakinamos ir neparduodamos, todėl laisvos vietos = prieinamos vietos.
    """
    eilutes = (
        Sale.objects.filter(id__in=set(sale_ids))
        .annotate(kiekis=Count("eiles__vietos", filter=Q(eiles__vietos__prieinama=True)))
        .values_list("id", "kiekis")
    )
    return dict(eilutes)


def sales_schema(sale):
    """SAL-02: salės eilės ir vietos su tipais ir būsenomis.

    1 sprinte būsena tik LAISVA arba NEPRIEINAMA (užimtos vietos atsiras 2 sprinte).
    """
    vietos = Vieta.objects.filter(eile__sale=sale).select_related("eile").order_by("eile__numeris", "numeris")
    eiles = {}
    for v in vietos:
        eiles.setdefault(v.eile.numeris, []).append({
            "id": v.id,
            "numeris": v.numeris,
            "tipas": v.tipas,
            "busena": "LAISVA" if v.prieinama else "NEPRIEINAMA",
        })
    return [{"numeris": nr, "vietos": vt} for nr, vt in eiles.items()]
