"""Architektūros taisyklės (2 namų darbas): komponentų priklausomybių kryptis ir kodo pasikartojimas."""
import ast
from pathlib import Path

import pytest
from rest_framework.test import APIRequestFactory

from naudotojai.models import Naudotojas
from naudotojai.permissions import AdminRasymui

BACKEND = Path(__file__).resolve().parents[1]


def _importuoti_moduliai(katalogas):
    """Visi moduliai, importuojami katalogo .py failuose (įskaitant importus funkcijų viduje)."""
    rasti = {}
    for kelias in (BACKEND / katalogas).rglob("*.py"):
        if "migrations" in kelias.parts:
            continue
        for mazgas in ast.walk(ast.parse(kelias.read_text(encoding="utf-8"))):
            if isinstance(mazgas, ast.Import):
                rasti.setdefault(kelias.name, set()).update(a.name.split(".")[0] for a in mazgas.names)
            elif isinstance(mazgas, ast.ImportFrom) and mazgas.level == 0 and mazgas.module:
                rasti.setdefault(kelias.name, set()).add(mazgas.module.split(".")[0])
    return rasti


def test_sales_komponentas_nepriklauso_nuo_repertuaro():
    """Ciklinė priklausomybė sales <-> repertuaras pašalinta: priklauso tik repertuaras nuo sales."""
    priklausomybes = _importuoti_moduliai("sales")
    pazeidimai = [failas for failas, moduliai in priklausomybes.items() if "repertuaras" in moduliai]
    assert pazeidimai == []


def test_repertuaras_naudoja_sales_viena_kryptimi():
    assert any("sales" in moduliai for moduliai in _importuoti_moduliai("repertuaras").values())


def _klasiu_apibrezimai(failas, klases_vardas):
    medis = ast.parse((BACKEND / failas).read_text(encoding="utf-8"))
    return [n for n in ast.walk(medis) if isinstance(n, ast.ClassDef) and n.name == klases_vardas]


@pytest.mark.parametrize("failas", ["sales/views.py", "repertuaras/views.py"])
def test_admin_rasymui_neapibreztas_pakartotinai(failas):
    assert _klasiu_apibrezimai(failas, "AdminRasymui") == []


@pytest.mark.django_db
@pytest.mark.parametrize("metodas,administratorius,tikimasi", [
    ("get", False, True), ("head", False, True), ("options", False, True),
    ("post", False, False), ("put", False, False), ("delete", False, False),
    ("post", True, True), ("put", True, True), ("delete", True, True),
])
def test_admin_rasymui_teises(metodas, administratorius, tikimasi):
    uzklausa = getattr(APIRequestFactory(), metodas)("/")
    uzklausa.user = Naudotojas.objects.create_user(
        email="x@test.lt", password="Kinas2026", vardas="X",
        role=Naudotojas.Role.ADMINISTRATORIUS if administratorius else Naudotojas.Role.KLIENTAS,
    )
    assert AdminRasymui().has_permission(uzklausa, None) is tikimasi
