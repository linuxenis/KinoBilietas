"""K5 Repertuaro komponento dalykinė logika."""
from datetime import datetime, time, timedelta

from django.utils import timezone

from sales.paslaugos import prieinamu_vietu_skaicius

from .models import Seansas

REPERTUARO_DIENOS = 14  # FR-01: nuo šiandien iki +13 d.


def busimi_seansai():
    """REP-01: tik SUPLANUOTI seansai, kurių pradžia vėlesnė nei dabar."""
    return (
        Seansas.objects.filter(busena=Seansas.Busena.SUPLANUOTAS, pradzia__gt=timezone.now())
        .select_related("filmas", "sale")
        .prefetch_related("kainos", "filmas__zanrai")
    )


def dienos_ribos(data):
    tz = timezone.get_current_timezone()
    pradzia = datetime.combine(data, time.min, tzinfo=tz)
    return pradzia, pradzia + timedelta(days=1)


def grupuoti_pagal_filma(seansai):
    """REP-01: seansai sugrupuojami pagal filmą, kiekvienam pridedamas laisvų vietų skaičius."""
    seansai = list(seansai)
    laisvos = prieinamu_vietu_skaicius(s.sale_id for s in seansai)
    filmai = {}
    for s in seansai:
        filmai.setdefault(s.filmas_id, {"filmas": s.filmas, "seansai": []})["seansai"].append((s, laisvos))
    return list(filmai.values())


def filtruoti(seansai, zanras=None, sale=None):
    """REP-02: atranka pagal žanrą ir salę (None reiškia „Visi“)."""
    if zanras:
        seansai = seansai.filter(filmas__zanrai__id=zanras)
    if sale:
        seansai = seansai.filter(sale_id=sale)
    return seansai.distinct()


def artimiausia_data(seansai, po):
    """REP-02: artimiausia data po nurodyto laiko, kurią yra filtrus atitinkantis seansas."""
    riba = timezone.localdate() + timedelta(days=REPERTUARO_DIENOS)
    kitas = seansai.filter(pradzia__gte=po).order_by("pradzia").first()
    if kitas is None:
        return None
    diena = timezone.localtime(kitas.pradzia).date()
    return diena if diena < riba else None
