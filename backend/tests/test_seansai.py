"""TA-01: seanso pabaigos skaičiavimas ir persidengimo tikrinimas (TC-10, TC-11, TC-12)."""
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from repertuaras.models import Seansas

pytestmark = pytest.mark.django_db


def _forma(d, **kita):
    forma = {
        "filmas": d["duna"].id, "sale": d["sale"].id,
        "data": (timezone.localdate() + timedelta(days=2)).isoformat(),
        "pradzia": "17:30", "formatas": "F2D", "kaina_suaugusiojo": "6.50", "kaina_studento": "5.00",
    }
    forma.update(kita)
    return forma


def test_seanso_pabaiga_apskaiciuojama(duomenys, admin_klientas):  # TC-10
    atsakas = admin_klientas.post("/api/v1/seansai", _forma(duomenys), format="json")
    assert atsakas.status_code == 201
    assert timezone.localtime(atsakas.data["pabaiga"]).strftime("%H:%M") == "20:31"  # 17:30 + 166 + 15


def test_persidengiantis_seansas_neissaugomas(duomenys, admin_klientas):  # TC-11
    admin_klientas.post("/api/v1/seansai", _forma(duomenys), format="json")
    pries = Seansas.objects.count()
    atsakas = admin_klientas.post("/api/v1/seansai", _forma(duomenys, pradzia="19:00"), format="json")
    assert atsakas.status_code == 409
    assert "Dūna: antroji dalis" in atsakas.data["bendra"]
    assert "17:30–20:31" in atsakas.data["bendra"]
    assert Seansas.objects.count() == pries  # duomenų bazėje naujo įrašo nėra


def test_kitoje_saleje_tuo_paciu_metu_galima(duomenys, admin_klientas):
    admin_klientas.post("/api/v1/seansai", _forma(duomenys), format="json")
    atsakas = admin_klientas.post("/api/v1/seansai", _forma(duomenys, sale=duomenys["sale2"].id), format="json")
    assert atsakas.status_code == 201


def test_seanso_praeityje_sukurti_negalima(duomenys, admin_klientas):
    vakar = (timezone.localdate() - timedelta(days=1)).isoformat()
    atsakas = admin_klientas.post("/api/v1/seansai", _forma(duomenys, data=vakar), format="json")
    assert atsakas.status_code == 400
    assert "pradzia" in atsakas.data


def test_suaugusiojo_kaina_privaloma(duomenys, admin_klientas):
    forma = _forma(duomenys)
    del forma["kaina_suaugusiojo"]
    assert admin_klientas.post("/api/v1/seansai", forma, format="json").status_code == 400


def test_seanso_atsaukimas(duomenys, admin_klientas):  # TC-12
    s = duomenys["s_duna"]
    atsakas = admin_klientas.post(f"/api/v1/seansai/{s.id}/atsaukti")
    assert atsakas.data["busena"] == "ATSAUKTAS"
    data = timezone.localtime(s.pradzia).date().isoformat()
    repertuaras = APIClient().get(f"/api/v1/seansai?data={data}").data
    assert all(f["pavadinimas"] != "Dūna: antroji dalis" for f in repertuaras["filmai"])


def test_klientas_negali_kurti_seanso(duomenys, kliento_klientas):
    assert kliento_klientas.post("/api/v1/seansai", _forma(duomenys), format="json").status_code == 403
