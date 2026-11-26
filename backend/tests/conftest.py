"""Bendri testų duomenys: salė, filmai, seansai."""
from datetime import datetime, time, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from naudotojai.models import Naudotojas
from repertuaras.models import Filmas, FilmuPlatintojas, Seansas, SeansoKaina, Zanras
from sales.models import Eile, KinoTeatras, Sale, Vieta


def rytoj_laiku(valanda, minute=0, dienos=1):
    tz = timezone.get_current_timezone()
    return datetime.combine(timezone.localdate() + timedelta(days=dienos), time(valanda, minute), tzinfo=tz)


def sukurti_seansa(filmas, sale, pradzia, suaugusiojo="6.50", busena=Seansas.Busena.SUPLANUOTAS):
    s = Seansas.objects.create(
        filmas=filmas, sale=sale, pradzia=pradzia,
        pabaiga=Seansas.apskaiciuoti_pabaiga(pradzia, filmas.trukme_min), busena=busena,
    )
    SeansoKaina.objects.create(seansas=s, bilieto_tipas="SUAUGUSIOJO", suma=Decimal(suaugusiojo))
    SeansoKaina.objects.create(seansas=s, bilieto_tipas="STUDENTO", suma=Decimal("5.00"))
    return s


@pytest.fixture
def duomenys(db):
    teatras = KinoTeatras.objects.create(pavadinimas="Testinis")
    sale = Sale.objects.create(kino_teatras=teatras, pavadinimas="1 salė")
    for e in range(1, 9):
        eile = Eile.objects.create(sale=sale, numeris=e)
        for v in range(1, 16):
            Vieta.objects.create(eile=eile, numeris=v, prieinama=not (e == 8 and v == 15))
    sale2 = Sale.objects.create(kino_teatras=teatras, pavadinimas="2 salė")
    eile = Eile.objects.create(sale=sale2, numeris=1)
    for v in range(1, 6):
        Vieta.objects.create(eile=eile, numeris=v)

    platintojas = FilmuPlatintojas.objects.create(pavadinimas="Platintojas")
    fantastika = Zanras.objects.create(pavadinimas="Fantastika")
    animacija = Zanras.objects.create(pavadinimas="Animacija")
    duna = Filmas.objects.create(pavadinimas="Dūna: antroji dalis", trukme_min=166, cenzas="N13", platintojas=platintojas)
    duna.zanrai.add(fantastika)
    robotas = Filmas.objects.create(pavadinimas="Laukinis robotas", trukme_min=102, cenzas="V", platintojas=platintojas)
    robotas.zanrai.add(animacija)

    return {
        "sale": sale, "sale2": sale2, "platintojas": platintojas,
        "fantastika": fantastika, "animacija": animacija, "duna": duna, "robotas": robotas,
        "s_duna": sukurti_seansa(duna, sale, rytoj_laiku(17, 30)),
        "s_robotas": sukurti_seansa(robotas, sale2, rytoj_laiku(12, 0)),
    }


@pytest.fixture
def admin_klientas(db):
    n = Naudotojas.objects.create_user(email="admin@test.lt", password="Admin2026", vardas="A",
                                       role=Naudotojas.Role.ADMINISTRATORIUS)
    k = APIClient()
    k.force_authenticate(n)
    return k


@pytest.fixture
def kliento_klientas(db):
    n = Naudotojas.objects.create_user(email="ona@test.lt", password="Kinas2026", vardas="Ona")
    k = APIClient()
    k.force_authenticate(n)
    return k
