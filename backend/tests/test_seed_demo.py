"""Demonstracinių duomenų komanda seed_demo (NFR-08): elgsenos fiksavimas prieš kodo pertvarkymą."""
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from naudotojai.models import Naudotojas
from repertuaras.models import Filmas, Seansas, SeansoKaina, Zanras
from sales.models import Sale

pytestmark = pytest.mark.django_db

SEANSU_SKAICIUS = 176  # 14 dienų x 3 salės pagal seed_demo tvarkaraščio algoritmą


@pytest.fixture(autouse=True)
def _laikinas_media(settings, tmp_path, monkeypatch):
    settings.MEDIA_ROOT = str(tmp_path)  # plakatai neturi būti kopijuojami į tikrą media katalogą
    monkeypatch.delenv("DEMO_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("DEMO_KLIENTO_SLAPTAZODIS", raising=False)


def _seed(*args):
    isvestis = StringIO()
    call_command("seed_demo", *args, stdout=isvestis)
    return isvestis.getvalue()


def test_sukuriami_visi_demonstraciniai_duomenys():
    isvestis = _seed()
    assert Sale.objects.count() == 3
    assert Filmas.objects.count() == 6
    assert Zanras.objects.count() == 8
    assert Seansas.objects.count() == SEANSU_SKAICIUS
    assert SeansoKaina.objects.count() == SEANSU_SKAICIUS * 3
    assert Naudotojas.objects.count() == 4
    assert f"{SEANSU_SKAICIUS} seansai" in isvestis


def test_pakartotinis_paleidimas_nieko_nekeicia():
    _seed()
    isvestis = _seed()
    assert "praleidžiama" in isvestis
    assert Filmas.objects.count() == 6
    assert Seansas.objects.count() == SEANSU_SKAICIUS


def test_is_naujo_perkuria_duomenis_be_dubliavimo():
    _seed()
    _seed("--is-naujo")
    assert Filmas.objects.count() == 6
    assert Sale.objects.count() == 3  # KinoTeatras trinamas kaskadiškai kartu su senomis salėmis
    assert Seansas.objects.count() == SEANSU_SKAICIUS
    assert Naudotojas.objects.count() == 4


def test_seansai_vienoje_sale_nepersidengia():
    _seed()
    for sale in Sale.objects.all():
        seansai = list(Seansas.objects.filter(sale=sale).order_by("pradzia"))
        for pries, po in zip(seansai, seansai[1:]):
            assert po.pradzia >= pries.pabaiga


def test_n18_filmai_rodomi_tik_vakare():
    _seed()
    n18 = Seansas.objects.filter(filmas__cenzas=Filmas.Cenzas.N18)
    assert n18.exists()
    assert all(timezone.localtime(s.pradzia).hour >= 20 for s in n18)


def test_3d_tik_duna_pirmoje_sale_su_priedu():
    _seed()
    pirma = Sale.objects.get(pavadinimas="1 salė")
    for s in Seansas.objects.select_related("filmas", "sale"):
        tikisi_3d = s.sale_id == pirma.id and s.filmas.pavadinimas.startswith("Dūna")
        assert (s.formatas == Seansas.Formatas.F3D) == tikisi_3d
        suaugusiojo = s.kainos.get(bilieto_tipas="SUAUGUSIOJO").suma
        assert suaugusiojo == (Decimal("8.50") if tikisi_3d else Decimal("6.50"))


def test_saliu_schemos_ir_neprieinamos_vietos():
    _seed()
    s1 = Sale.objects.get(pavadinimas="1 salė")
    assert s1.talpa == 8 * 15 - 1
    assert Sale.objects.get(pavadinimas="2 salė").talpa == 6 * 12
    assert Sale.objects.get(pavadinimas="VIP salė").talpa == 4 * 8


def test_numatytieji_slaptazodziai():
    _seed()
    assert Naudotojas.objects.get(email="admin@kinobilietas.lt").check_password("Admin2026")
    assert Naudotojas.objects.get(email="ona@pavyzdys.lt").check_password("Kinas2026")


def test_administratoriaus_slaptazodis_imamas_is_aplinkos(monkeypatch):
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "Kitas2026x")
    _seed()
    admin = Naudotojas.objects.get(email="admin@kinobilietas.lt")
    assert admin.check_password("Kitas2026x")
    assert admin.role == Naudotojas.Role.ADMINISTRATORIUS
