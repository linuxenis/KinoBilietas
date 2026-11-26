"""K3 REST API ir K5 Repertuaro komponentas."""
from datetime import date, timedelta

from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from naudotojai.permissions import AdminRasymui, YraAdministratorius
from sales.paslaugos import sales_schema

from . import paslaugos, seansai as seansu_paslaugos
from .models import Filmas, FilmuPlatintojas, Seansas, Zanras
from .serializers import (
    FilmoFormaSerializer,
    FilmoInformacijaSerializer,
    RepertuaroFilmasSerializer,
    SeansoFormaSerializer,
    seanso_administravimui,
    seanso_eilute,
)


def _repertuaro_data(tekstas):
    siandien = timezone.localdate()
    if not tekstas:
        return siandien, None
    try:
        reiksme = date.fromisoformat(tekstas)
    except ValueError:
        return None, "Data turi būti formatu MMMM-MM-DD."
    if not siandien <= reiksme <= siandien + timedelta(days=paslaugos.REPERTUARO_DIENOS - 1):
        return None, "Repertuarą galima peržiūrėti nuo šiandien iki 13 dienų į priekį."
    return reiksme, None


def _filmu_sarasas(grupes):
    rezultatas = []
    for g in grupes:
        filmas = RepertuaroFilmasSerializer(g["filmas"]).data
        filmas["seansai"] = [seanso_eilute(s, laisvos) for s, laisvos in g["seansai"]]
        rezultatas.append(filmas)
    return rezultatas


def _sveikas_skaicius(tekstas):
    try:
        return int(tekstas) if tekstas not in (None, "", "visi") else None
    except ValueError:
        return None


def _issaugoti_seansa(request, seansas=None):
    s = SeansoFormaSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    try:
        objektas = seansu_paslaugos.issaugoti_seansa(s.validated_data, seansas=seansas)
    except seansu_paslaugos.SeansoKlaida as k:
        return Response({**k.laukai, "konfliktas": k.konfliktas}, status=k.statusas)
    objektas = Seansas.objects.select_related("filmas", "sale").prefetch_related("kainos").get(pk=objektas.pk)
    return Response(seanso_administravimui(objektas), status=200 if seansas else 201)


@api_view(["GET", "POST"])
@permission_classes([AdminRasymui])
def repertuaras(request):
    """API-01 / FR-01, FR-02: GET /api/v1/seansai?data=MMMM-MM-DD&zanras=ID&sale=ID
    API-03 / FR-07: POST /api/v1/seansai (tik administratoriui)."""
    if request.method == "POST":
        return _issaugoti_seansa(request)

    data, klaida = _repertuaro_data(request.query_params.get("data"))
    if klaida:
        return Response({"klaida": klaida}, status=400)
    zanras = _sveikas_skaicius(request.query_params.get("zanras"))
    sale = _sveikas_skaicius(request.query_params.get("sale"))

    filtruoti = paslaugos.filtruoti(paslaugos.busimi_seansai(), zanras=zanras, sale=sale)
    nuo, iki = paslaugos.dienos_ribos(data)
    grupes = paslaugos.grupuoti_pagal_filma(filtruoti.filter(pradzia__gte=nuo, pradzia__lt=iki))

    artimiausia = None
    if not grupes:
        artimiausia = paslaugos.artimiausia_data(filtruoti, po=iki)
    return Response({
        "data": data.isoformat(),
        "filmai": _filmu_sarasas(grupes),
        "artimiausia_data": artimiausia.isoformat() if artimiausia else None,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def zanrai(request):
    """ZS-02: žanrų sąrašas filtrui ir filmo formai."""
    return Response([{"id": z.id, "pavadinimas": z.pavadinimas} for z in Zanras.objects.all()])


@api_view(["GET"])
@permission_classes([YraAdministratorius])
def platintojai(request):
    return Response([{"id": p.id, "pavadinimas": p.pavadinimas} for p in FilmuPlatintojas.objects.all()])


def _filmo_informacija(request, filmas):
    """REP-03 / FR-03: filmo duomenys ir seansai artimiausioms 14 d."""
    riba = paslaugos.dienos_ribos(timezone.localdate() + timedelta(days=paslaugos.REPERTUARO_DIENOS - 1))[1]
    seansai = paslaugos.busimi_seansai().filter(filmas=filmas, pradzia__lt=riba)
    grupes = paslaugos.grupuoti_pagal_filma(seansai)
    duomenys = FilmoInformacijaSerializer(filmas).data
    duomenys["seansai"] = [seanso_eilute(s, laisvos) for s, laisvos in grupes[0]["seansai"]] if grupes else []
    return Response(duomenys)


@api_view(["GET", "POST"])
@permission_classes([YraAdministratorius])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def filmai(request):
    """API-02: GET (administravimo sąrašas) ir POST /api/v1/filmai."""
    if request.method == "POST":
        s = FilmoFormaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        filmas = s.save()
        return Response(FilmoFormaSerializer(filmas).data, status=201)
    qs = Filmas.objects.prefetch_related("zanrai").select_related("platintojas")
    return Response(FilmoFormaSerializer(qs, many=True).data)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AdminRasymui])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def filmas(request, pk):
    """GET viešai (FR-03), PUT ir DELETE tik administratoriui (FR-06, API-02)."""
    objektas = get_object_or_404(Filmas.objects.prefetch_related("zanrai"), pk=pk)
    if request.method == "GET":
        return _filmo_informacija(request, objektas)

    if request.method == "PUT":
        s = FilmoFormaSerializer(objektas, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)

    # REP-04: filmo, turinčio būsimų seansų, pašalinti neleidžiama
    busimi = objektas.seansai.filter(busena=Seansas.Busena.SUPLANUOTAS, pradzia__gt=timezone.now()).count()
    if busimi:
        return Response(
            {"klaida": f"Filmo „{objektas.pavadinimas}“ pašalinti negalima: jis turi būsimų seansų ({busimi}). "
                       "Pirmiausia atšaukite seansus."},
            status=409,
        )
    try:
        objektas.delete()
    except ProtectedError:
        return Response(
            {"klaida": f"Filmo „{objektas.pavadinimas}“ pašalinti negalima: jis turi seansų istoriją."},
            status=409,
        )
    return Response(status=204)


@api_view(["GET"])
@permission_classes([YraAdministratorius])
def seansu_valdymas(request):
    """AS-02, AS-03: administravimo seansų sąrašas pasirinktai datai (numatytoji šiandien)."""
    try:
        data = date.fromisoformat(request.query_params.get("data") or timezone.localdate().isoformat())
    except ValueError:
        return Response({"klaida": "Data turi būti formatu MMMM-MM-DD."}, status=400)
    nuo, iki = paslaugos.dienos_ribos(data)
    qs = (
        Seansas.objects.filter(pradzia__gte=nuo, pradzia__lt=iki)
        .select_related("filmas", "sale").prefetch_related("kainos").order_by("sale__pavadinimas", "pradzia")
    )
    return Response([seanso_administravimui(s) for s in qs])


@api_view(["GET", "PUT"])
@permission_classes([YraAdministratorius])
def seansas(request, pk):
    """FR-08 / AS-03: seanso redagavimas."""
    objektas = get_object_or_404(Seansas.objects.select_related("filmas", "sale").prefetch_related("kainos"), pk=pk)
    if request.method == "GET":
        return Response(seanso_administravimui(objektas))
    if objektas.busena == Seansas.Busena.ATSAUKTAS:
        return Response({"bendra": "Atšaukto seanso redaguoti negalima."}, status=409)
    return _issaugoti_seansa(request, seansas=objektas)


@api_view(["POST"])
@permission_classes([YraAdministratorius])
def seanso_atsaukimas(request, pk):
    """FR-08 / REP-07: POST /api/v1/seansai/{id}/atsaukti"""
    objektas = get_object_or_404(Seansas, pk=pk)
    seansu_paslaugos.atsaukti(objektas)
    objektas = Seansas.objects.select_related("filmas", "sale").prefetch_related("kainos").get(pk=pk)
    return Response(seanso_administravimui(objektas))


@api_view(["GET"])
@permission_classes([AllowAny])
def seanso_schema(request, pk):
    """ZS-04 / SAL-02 / FR-04: GET /api/v1/seansai/{id}/schema"""
    seansas = get_object_or_404(
        Seansas.objects.select_related("filmas", "sale").prefetch_related("kainos"),
        pk=pk, busena=Seansas.Busena.SUPLANUOTAS,
    )
    kainos = {k.bilieto_tipas: str(k.suma) for k in seansas.kainos.all()}
    return Response({
        "seansas": {
            "id": seansas.id,
            "filmas": seansas.filmas.pavadinimas,
            "filmas_id": seansas.filmas_id,
            "pradzia": seansas.pradzia,
            "formatas": seansas.formatas,
            "sale": seansas.sale.pavadinimas,
            "suaugusiojo_kaina": kainos.get("SUAUGUSIOJO"),
        },
        "eiles": sales_schema(seansas.sale),
    })
