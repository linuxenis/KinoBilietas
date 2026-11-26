"""TA-02: salės duomenų tikrinimas (TC-13) ir SAL-04."""
import pytest

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
