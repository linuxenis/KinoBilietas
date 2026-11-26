"""Salių redagavimo logikos moduliniai testai (po pertvarkymo: sales/redagavimas.py, sales/serializers.py)."""
import pytest

from sales import redagavimas
from sales.models import NEPRIEINAMA, Vieta
from sales.serializers import SalesFormaSerializer

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("tipas_formoje,tikimasi", [
    ("STANDARTINE", (Vieta.Tipas.STANDARTINE, True)),
    ("NEIGALIESIEMS", (Vieta.Tipas.NEIGALIESIEMS, True)),
    (NEPRIEINAMA, (Vieta.Tipas.STANDARTINE, False)),
])
def test_vietos_savybes_pagal_formos_tipa(tipas_formoje, tikimasi):
    assert redagavimas._vietos_savybes(tipas_formoje) == tikimasi


def test_sukurimas_taiko_tipus_is_formos():
    sale = redagavimas.sukurti({
        "pavadinimas": "Bandomoji", "eiliu": 2, "vietu": 3,
        "vietos": [{"eile": 1, "vieta": 2, "tipas": "NEIGALIESIEMS"}, {"eile": 2, "vieta": 3, "tipas": NEPRIEINAMA}],
    })
    vietos = {(v.eile.numeris, v.numeris): v for v in Vieta.objects.filter(eile__sale=sale).select_related("eile")}
    assert len(vietos) == 6
    assert vietos[(1, 2)].tipas == "NEIGALIESIEMS" and vietos[(1, 2)].prieinama
    assert vietos[(2, 3)].tipas == "STANDARTINE" and not vietos[(2, 3)].prieinama
    assert vietos[(1, 1)].tipas == "STANDARTINE" and vietos[(1, 1)].prieinama


def test_vietu_tipu_atnaujinimas_nekuria_uzklausos_kiekvienai_vietai(duomenys, django_assert_max_num_queries):
    sale = duomenys["sale"]  # 8 x 15 = 120 vietų
    forma = {"pavadinimas": "1 salė", "eiliu": 8, "vietu": 15,
             "vietos": [{"eile": 1, "vieta": 1, "tipas": NEPRIEINAMA}]}
    with django_assert_max_num_queries(40):  # prieš pertvarkymą: ~120 atskirų UPDATE užklausų
        redagavimas.atnaujinti(sale, forma)
    assert Vieta.objects.filter(eile__sale=sale, prieinama=False).count() == 1


def test_formos_tipu_pasirinkimai_apima_modelio_tipus_ir_neprieinama():
    s = SalesFormaSerializer(data={"pavadinimas": "A", "eiliu": 1, "vietu": 1,
                                   "vietos": [{"eile": 1, "vieta": 1, "tipas": "NERA"}]})
    assert not s.is_valid()
    pasirinkimai = set(SalesFormaSerializer().fields["vietos"].child.fields["tipas"].choices)
    assert pasirinkimai == {*Vieta.Tipas.values, NEPRIEINAMA}
