"""TA-03: repertuaro, filmo ir schemos API užklausos."""
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from repertuaras.models import Seansas

from .conftest import rytoj_laiku, sukurti_seansa

pytestmark = pytest.mark.django_db


def _rytoj():
    return (timezone.localdate() + timedelta(days=1)).isoformat()


def test_repertuaras_rodo_tik_suplanuotus_seansus(duomenys):  # TC-01
    sukurti_seansa(duomenys["duna"], duomenys["sale"], rytoj_laiku(21, 0), busena=Seansas.Busena.ATSAUKTAS)
    atsakas = APIClient().get(f"/api/v1/seansai?data={_rytoj()}")
    assert atsakas.status_code == 200
    filmai = {f["pavadinimas"]: f for f in atsakas.data["filmai"]}
    assert set(filmai) == {"Dūna: antroji dalis", "Laukinis robotas"}
    duna_seansai = filmai["Dūna: antroji dalis"]["seansai"]
    assert len(duna_seansai) == 1  # atšauktas nerodomas
    assert duna_seansai[0]["maziausia_kaina"] == "5.00"
    assert duna_seansai[0]["laisvos_vietos"] == 119  # 8 x 15, viena neprieinama


def test_repertuaras_netinkama_data(duomenys):
    atsakas = APIClient().get("/api/v1/seansai?data=2000-01-01")
    assert atsakas.status_code == 400


def test_filtras_pagal_zanra(duomenys):  # TC-02
    atsakas = APIClient().get(f"/api/v1/seansai?data={_rytoj()}&zanras={duomenys['animacija'].id}")
    assert [f["pavadinimas"] for f in atsakas.data["filmai"]] == ["Laukinis robotas"]


def test_filtras_be_rezultatu_siulo_artimiausia_data(duomenys):  # TC-03
    siaubo = duomenys["fantastika"]
    sukurti_seansa(duomenys["duna"], duomenys["sale2"], rytoj_laiku(18, 0, dienos=3))
    atsakas = APIClient().get(
        f"/api/v1/seansai?data={_rytoj()}&zanras={siaubo.id}&sale={duomenys['sale2'].id}"
    )
    assert atsakas.data["filmai"] == []
    assert atsakas.data["artimiausia_data"] == (timezone.localdate() + timedelta(days=3)).isoformat()


def test_filmo_puslapis(duomenys):  # TC-04
    duna = duomenys["duna"]
    sukurti_seansa(duna, duomenys["sale"], rytoj_laiku(18, 0, dienos=20))  # už 14 d. ribos
    atsakas = APIClient().get(f"/api/v1/filmai/{duna.id}")
    assert atsakas.status_code == 200
    assert atsakas.data["trukme_min"] == 166
    assert atsakas.data["cenzas_rodomas"] == "N-13"
    assert atsakas.data["zanrai"] == ["Fantastika"]
    assert len(atsakas.data["seansai"]) == 1


def test_sales_schema(duomenys):  # TC-05
    atsakas = APIClient().get(f"/api/v1/seansai/{duomenys['s_duna'].id}/schema")
    assert atsakas.status_code == 200
    eiles = atsakas.data["eiles"]
    assert len(eiles) == 8 and all(len(e["vietos"]) == 15 for e in eiles)
    assert eiles[7]["vietos"][14]["busena"] == "NEPRIEINAMA"
    assert atsakas.data["seansas"]["suaugusiojo_kaina"] == "6.50"
