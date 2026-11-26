"""TA-04: registracija, prisijungimas, užrakinimas, atsijungimas ir rolės."""
import pytest
from rest_framework.test import APIClient

from naudotojai.models import Naudotojas

pytestmark = pytest.mark.django_db

REG = "/api/v1/auth/registracija"
PRIS = "/api/v1/auth/prisijungimas"


def _registruoti(klientas, **kita):
    duomenys = {"vardas": "Ona", "email": "ona@test.lt", "slaptazodis": "Kinas2026",
                "slaptazodis2": "Kinas2026", "sutikimas": True}
    duomenys.update(kita)
    return klientas.post(REG, duomenys, format="json")


def test_registracija_sukuria_klienta_ir_prijungia():  # TC-14
    atsakas = _registruoti(APIClient())
    assert atsakas.status_code == 201
    assert atsakas.data["prieigos"]
    assert atsakas.data["naudotojas"]["role"] == "KLIENTAS"


def test_registracija_be_sutikimo_atmetama():  # TC-15
    atsakas = _registruoti(APIClient(), sutikimas=False)
    assert atsakas.status_code == 400
    assert "sutikimas" in atsakas.data
    assert not Naudotojas.objects.exists()


def test_registracija_silpnas_slaptazodis_ir_dubliuotas_pastas():
    k = APIClient()
    assert _registruoti(k, slaptazodis="trumpas", slaptazodis2="trumpas").status_code == 400
    assert _registruoti(k).status_code == 201
    assert _registruoti(k).status_code == 400


def test_prisijungimas_administratoriaus_role():  # TC-16
    Naudotojas.objects.create_user(email="admin@test.lt", password="Admin2026", vardas="A",
                                   role=Naudotojas.Role.ADMINISTRATORIUS)
    atsakas = APIClient().post(PRIS, {"email": "admin@test.lt", "slaptazodis": "Admin2026"}, format="json")
    assert atsakas.status_code == 200
    assert atsakas.data["naudotojas"]["role"] == "ADMINISTRATORIUS"


def test_uzrakinimas_po_5_bandymu():  # TC-17
    Naudotojas.objects.create_user(email="ona@test.lt", password="Kinas2026", vardas="Ona")
    k = APIClient()
    for _ in range(4):
        assert k.post(PRIS, {"email": "ona@test.lt", "slaptazodis": "blogas1"}, format="json").status_code == 401
    assert k.post(PRIS, {"email": "ona@test.lt", "slaptazodis": "blogas1"}, format="json").status_code == 423
    # Net teisingas slaptažodis neveikia, kol paskyra užrakinta
    assert k.post(PRIS, {"email": "ona@test.lt", "slaptazodis": "Kinas2026"}, format="json").status_code == 423


def test_atsijungimas_panaikina_atnaujinimo_zetona():  # TC-18
    k = APIClient()
    zetonai = _registruoti(k).data
    k.credentials(HTTP_AUTHORIZATION=f"Bearer {zetonai['prieigos']}")
    assert k.post("/api/v1/auth/atsijungimas", {"atnaujinimo": zetonai["atnaujinimo"]}, format="json").status_code == 204
    atsakas = APIClient().post("/api/v1/auth/atnaujinti", {"refresh": zetonai["atnaujinimo"]}, format="json")
    assert atsakas.status_code == 401
