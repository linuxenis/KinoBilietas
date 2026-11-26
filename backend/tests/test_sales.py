"""TA-02: salės duomenų tikrinimas (TC-13) ir SAL-04."""
import pytest
from rest_framework.test import APIClient

from sales.models import Sale

pytestmark = pytest.mark.django_db


def test_sales_kurimas_su_neprieinama_vieta(admin_klientas):  # TC-13
    atsakas = admin_klientas.post("/api/v1/sales", {
        "pavadinimas": "3 salė", "eiliu": 8, "vietu": 10,
        "vietos": [
            {"eile": 8, "vieta": 10, "tipas": "NEPRIEINAMA"},
            {"eile": 1, "vieta": 1, "tipas": "NEIGALIESIEMS"},
        ],
    }, format="json")
    assert atsakas.status_code == 201
    assert atsakas.data["talpa"] == 79
    vietos = [v for e in atsakas.data["eiles"] for v in e["vietos"]]
    assert len(vietos) == 80


def test_netinkami_matmenys(admin_klientas):
    atsakas = admin_klientas.post("/api/v1/sales", {"pavadinimas": "", "eiliu": 31, "vietu": 0}, format="json")
    assert atsakas.status_code == 400
    assert {"pavadinimas", "eiliu", "vietu"} <= set(atsakas.data)


def test_sales_su_busimais_seansais_strukturos_keisti_negalima(duomenys, admin_klientas):
    sale = duomenys["sale"]
    atsakas = admin_klientas.put(
        f"/api/v1/sales/{sale.id}", {"pavadinimas": "1 salė", "eiliu": 9, "vietu": 15}, format="json"
    )
    assert atsakas.status_code == 409
    assert Sale.objects.get(pk=sale.id).eiles.count() == 8


def test_vietu_tipus_keisti_galima_ir_su_seansais(duomenys, admin_klientas):
    sale = duomenys["sale"]
    atsakas = admin_klientas.put(f"/api/v1/sales/{sale.id}", {
        "pavadinimas": "1 salė", "eiliu": 8, "vietu": 15,
        "vietos": [{"eile": 1, "vieta": 1, "tipas": "NEPRIEINAMA"}],
    }, format="json")
    assert atsakas.status_code == 200
    assert atsakas.data["talpa"] == 119  # 8 x 15 = 120, viena neprieinama


def test_klientas_negali_kurti_sales(kliento_klientas):
    atsakas = kliento_klientas.post("/api/v1/sales", {"pavadinimas": "X", "eiliu": 1, "vietu": 1}, format="json")
    assert atsakas.status_code == 403


# --- Papildyta prieš kodo pertvarkymą (2 namų darbas) ---
from sales.models import Vieta  # noqa: E402


def _tipai_pagal_vieta(sale):
    return {
        (v.eile.numeris, v.numeris): (v.tipas, v.prieinama)
        for v in Vieta.objects.filter(eile__sale=sale).select_related("eile")
    }


def test_vietu_tipai_issaugomi_atnaujinant(duomenys, admin_klientas):
    sale = duomenys["sale"]
    atsakas = admin_klientas.put(f"/api/v1/sales/{sale.id}", {
        "pavadinimas": "1 salė", "eiliu": 8, "vietu": 15,
        "vietos": [
            {"eile": 2, "vieta": 3, "tipas": "NEIGALIESIEMS"},
            {"eile": 4, "vieta": 5, "tipas": "NEPRIEINAMA"},
        ],
    }, format="json")
    assert atsakas.status_code == 200
    tipai = _tipai_pagal_vieta(sale)
    assert tipai[(2, 3)] == ("NEIGALIESIEMS", True)
    assert tipai[(4, 5)] == ("STANDARTINE", False)
    # Anksčiau neprieinama vieta (8, 15) lieka standartine ir tampa prieinama, nes forma jos nebemini
    assert tipai[(8, 15)] == ("STANDARTINE", True)
    assert sum(1 for t in tipai.values() if t[1]) == 119


def test_sales_pavadinimas_atnaujinamas(duomenys, admin_klientas):
    sale = duomenys["sale"]
    admin_klientas.put(f"/api/v1/sales/{sale.id}", {"pavadinimas": "Nauja", "eiliu": 8, "vietu": 15}, format="json")
    sale.refresh_from_db()
    assert sale.pavadinimas == "Nauja"


def test_struktura_keiciama_kai_nera_busimu_seansu(admin_klientas):
    sukurta = admin_klientas.post("/api/v1/sales", {"pavadinimas": "Maža", "eiliu": 2, "vietu": 3}, format="json")
    assert sukurta.status_code == 201
    atsakas = admin_klientas.put(f"/api/v1/sales/{sukurta.data['id']}", {
        "pavadinimas": "Maža", "eiliu": 3, "vietu": 4,
        "vietos": [{"eile": 1, "vieta": 1, "tipas": "NEIGALIESIEMS"}],
    }, format="json")
    assert atsakas.status_code == 200
    assert (atsakas.data["eiliu"], atsakas.data["vietu"], atsakas.data["talpa"]) == (3, 4, 12)
    assert atsakas.data["turi_busimu_seansu"] is False
    assert atsakas.data["eiles"][0]["vietos"][0]["tipas"] == "NEIGALIESIEMS"


def test_vieta_uz_sales_ribu_atmetama(admin_klientas):
    atsakas = admin_klientas.post("/api/v1/sales", {
        "pavadinimas": "X", "eiliu": 2, "vietu": 2, "vietos": [{"eile": 3, "vieta": 1, "tipas": "NEPRIEINAMA"}],
    }, format="json")
    assert atsakas.status_code == 400
    assert "vietos" in atsakas.data


def test_sales_duomenyse_nurodoma_ar_yra_busimu_seansu(duomenys, admin_klientas):
    atsakas = admin_klientas.get(f"/api/v1/sales/{duomenys['sale'].id}")
    assert atsakas.status_code == 200
    assert atsakas.data["turi_busimu_seansu"] is True


def test_seanso_schema_viesa_ir_grazina_kainas(duomenys):
    seansas = duomenys["s_duna"]
    atsakas = APIClient().get(f"/api/v1/seansai/{seansas.id}/schema")
    assert atsakas.status_code == 200
    assert atsakas.data["seansas"]["suaugusiojo_kaina"] == "6.50"
    assert atsakas.data["seansas"]["sale"] == "1 salė"
    assert len(atsakas.data["eiles"]) == 8


def test_atsauktas_seansas_neturi_schemos(duomenys, admin_klientas):
    seansas = duomenys["s_duna"]
    admin_klientas.post(f"/api/v1/seansai/{seansas.id}/atsaukti")
    assert APIClient().get(f"/api/v1/seansai/{seansas.id}/schema").status_code == 404
