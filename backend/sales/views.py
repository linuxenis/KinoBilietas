"""K3 REST API ir K6 Salių komponentas (nepriklauso nuo K5 Repertuaro komponento)."""
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from naudotojai.permissions import AdminRasymui, YraAdministratorius

from . import redagavimas
from .models import Sale
from .paslaugos import sales_schema
from .serializers import SalesFormaSerializer


def _sales_duomenys(sale):
    eiliu, vietu = redagavimas.matmenys(sale)
    return {
        "id": sale.id,
        "pavadinimas": sale.pavadinimas,
        "eiliu": eiliu,
        "vietu": vietu,
        "talpa": sale.talpa,
        "turi_busimu_seansu": redagavimas.turi_busimu_seansu(sale),
        "eiles": sales_schema(sale),
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def kino_teatras(request):
    """NFR-10: kino teatro pavadinimas, adresas ir kontaktai iš konfigūracijos."""
    return Response(settings.KINO_TEATRAS)


@api_view(["GET", "POST"])
@permission_classes([AdminRasymui])
def saliu_sarasas(request):
    """GET: salių sąrašas (ZS-02). POST: naujos salės kūrimas (API-04, SAL-03)."""
    if request.method == "POST":
        s = SalesFormaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(_sales_duomenys(redagavimas.sukurti(s.validated_data)), status=201)
    return Response([{"id": s.id, "pavadinimas": s.pavadinimas, "talpa": s.talpa} for s in Sale.objects.all()])


@api_view(["GET", "PUT"])
@permission_classes([YraAdministratorius])
def sale(request, pk):
    """API-04: salės schema redaktoriui ir jos keitimas (SAL-04)."""
    objektas = get_object_or_404(Sale, pk=pk)
    if request.method == "GET":
        return Response(_sales_duomenys(objektas))
    s = SalesFormaSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    try:
        objektas = redagavimas.atnaujinti(objektas, s.validated_data)
    except redagavimas.SalesKlaida as k:
        return Response({"bendra": k.zinute}, status=409)
    return Response(_sales_duomenys(objektas))
