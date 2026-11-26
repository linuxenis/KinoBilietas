"""TA-02: filmo duomenų tikrinimas (TC-08, TC-09) ir prieigos ribojimas (TC-19)."""
import pytest

from repertuaras.models import Filmas

pytestmark = pytest.mark.django_db


def _forma(d, **kita):
    forma = {"pavadinimas": "Naujas filmas", "trukme_min": 120, "cenzas": "N7",
             "zanrai": [d["animacija"].id], "platintojas": d["platintojas"].id}
    forma.update(kita)
    return forma


def test_filmo_kurimas(duomenys, admin_klientas):
    atsakas = admin_klientas.post("/api/v1/filmai", _forma(duomenys), format="json")
    assert atsakas.status_code == 201
    assert Filmas.objects.filter(pavadinimas="Naujas filmas").exists()


def test_filmas_be_pavadinimo(duomenys, admin_klientas):  # TC-08
    atsakas = admin_klientas.post("/api/v1/filmai", _forma(duomenys, pavadinimas=""), format="json")
    assert atsakas.status_code == 400
    assert atsakas.data["pavadinimas"][0] == "Įveskite filmo pavadinimą."


def test_filmas_be_zanru_ir_per_ilgas(duomenys, admin_klientas):
    atsakas = admin_klientas.post("/api/v1/filmai", _forma(duomenys, zanrai=[], trukme_min=401), format="json")
    assert atsakas.status_code == 400
    assert "zanrai" in atsakas.data and "trukme_min" in atsakas.data


def test_filmo_su_busimu_seansu_salinti_negalima(duomenys, admin_klientas):  # TC-09
    atsakas = admin_klientas.delete(f"/api/v1/filmai/{duomenys['duna'].id}")
    assert atsakas.status_code == 409
    assert Filmas.objects.filter(pk=duomenys["duna"].id).exists()


def test_filmo_be_seansu_salinimas(duomenys, admin_klientas):
    naujas = admin_klientas.post("/api/v1/filmai", _forma(duomenys), format="json").data
    assert admin_klientas.delete(f"/api/v1/filmai/{naujas['id']}").status_code == 204


def test_filmo_redagavimas(duomenys, admin_klientas):
    atsakas = admin_klientas.put(f"/api/v1/filmai/{duomenys['duna'].id}", {"trukme_min": 170}, format="json")
    assert atsakas.status_code == 200
    duomenys["duna"].refresh_from_db()
    assert duomenys["duna"].trukme_min == 170


def test_klientas_negali_kurti_filmo(duomenys, kliento_klientas):  # TC-19
    atsakas = kliento_klientas.post("/api/v1/filmai", _forma(duomenys), format="json")
    assert atsakas.status_code == 403
    assert not Filmas.objects.filter(pavadinimas="Naujas filmas").exists()
