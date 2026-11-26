"""Paskyros užrakinimo logika Naudotojas modelyje (iškelta iš prisijungimo view po pertvarkymo)."""
from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone

from naudotojai.models import Naudotojas

pytestmark = pytest.mark.django_db


@pytest.fixture
def ona(db):
    return Naudotojas.objects.create_user(email="ona@test.lt", password="Kinas2026", vardas="Ona")


def test_neuzrakinta_paskyra(ona):
    assert not ona.yra_uzrakintas(timezone.now())


def test_uzrakinta_kol_nepasibaige_laikas(ona):
    dabar = timezone.now()
    ona.uzrakinta_iki = dabar + timedelta(minutes=1)
    assert ona.yra_uzrakintas(dabar)
    assert not ona.yra_uzrakintas(dabar + timedelta(minutes=2))


def test_likusios_minutes_apvalinamos_i_virsu(ona):
    dabar = timezone.now()
    ona.uzrakinta_iki = dabar + timedelta(minutes=10, seconds=30)
    assert ona.liko_uzrakinta_min(dabar) == 11


def test_gali_prisijungti_tik_su_teisingu_slaptazodziu_ir_aktyvia_paskyra(ona):
    assert ona.gali_prisijungti("Kinas2026")
    assert not ona.gali_prisijungti("blogas")
    ona.is_active = False
    assert not ona.gali_prisijungti("Kinas2026")


def test_nesekme_didina_skaitikli_bet_neuzrakina_pries_riba(ona):
    dabar = timezone.now()
    assert ona.uzregistruoti_nesekminga(dabar) is False
    ona.refresh_from_db()
    assert ona.nesekmingi_bandymai == 1
    assert ona.uzrakinta_iki is None


def test_pasiekus_riba_paskyra_uzrakinama_ir_skaitiklis_nunulinamas(ona):
    dabar = timezone.now()
    ona.nesekmingi_bandymai = settings.PRISIJUNGIMO_BANDYMAI - 1
    assert ona.uzregistruoti_nesekminga(dabar) is True
    ona.refresh_from_db()
    assert ona.nesekmingi_bandymai == 0
    assert ona.uzrakinta_iki == dabar + settings.UZRAKINIMO_TRUKME


def test_sekme_isvalo_busena_ir_uzregistruoja_prisijungima(ona):
    dabar = timezone.now()
    ona.nesekmingi_bandymai = 3
    ona.uzrakinta_iki = dabar - timedelta(minutes=1)
    ona.uzregistruoti_sekminga(dabar)
    ona.refresh_from_db()
    assert (ona.nesekmingi_bandymai, ona.uzrakinta_iki, ona.last_login) == (0, None, dabar)
