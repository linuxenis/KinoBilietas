"""K4 Autentifikacijos komponentas: FR-10, FR-11, FR-12."""
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Naudotojas
from .serializers import NaudotojasSerializer, PrisijungimasSerializer, RegistracijaSerializer


def _zetonai(naudotojas):
    refresh = RefreshToken.for_user(naudotojas)
    return {
        "prieigos": str(refresh.access_token),
        "atnaujinimo": str(refresh),
        "naudotojas": NaudotojasSerializer(naudotojas).data,
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def registracija(request):
    """API-05 / AUT-01: sukuria kliento paskyrą ir iškart prijungia."""
    s = RegistracijaSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    d = s.validated_data
    naudotojas = Naudotojas.objects.create_user(
        email=d["email"], password=d["slaptazodis"], vardas=d["vardas"],
        sutikimas_su_politika=True, sutikimo_data=timezone.now(),
    )
    return Response(_zetonai(naudotojas), status=status.HTTP_201_CREATED)


BENDRA_KLAIDA = "Neteisingas el. paštas arba slaptažodis."


def _uzrakinta(zinute):
    return Response({"klaida": zinute, "uzrakinta": True}, status=status.HTTP_423_LOCKED)


def _neteisingi_duomenys(papildymas=""):
    return Response({"klaida": BENDRA_KLAIDA + papildymas}, status=status.HTTP_401_UNAUTHORIZED)


def _bandymu_zodis(kiekis):
    return "bandymas" if kiekis == 1 else "bandymai"


def _nesekmingas_bandymas(naudotojas, dabar):
    """Užregistruoja nesėkmę ir sudaro atsakymą: užrakinta (423) arba likusių bandymų pranešimas (401)."""
    riba = settings.PRISIJUNGIMO_BANDYMAI
    if naudotojas.uzregistruoti_nesekminga(dabar):
        minutes = int(settings.UZRAKINIMO_TRUKME.total_seconds() // 60)
        return _uzrakinta(f"Paskyra laikinai užrakinta {minutes} min. po {riba} nesėkmingų bandymų.")
    liko = riba - naudotojas.nesekmingi_bandymai
    return _neteisingi_duomenys(f" Liko {liko} {_bandymu_zodis(liko)}.")


@api_view(["POST"])
@permission_classes([AllowAny])
def prisijungimas(request):
    """API-06 / AUT-02: tikrina duomenis, po 5 nesėkmingų bandymų užrakina 15 min."""
    s = PrisijungimasSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    email = s.validated_data["email"].lower()
    slaptazodis = s.validated_data["slaptazodis"]

    naudotojas = Naudotojas.objects.filter(email=email).first()
    if naudotojas is None:
        return _neteisingi_duomenys()

    dabar = timezone.now()
    if naudotojas.yra_uzrakintas(dabar):
        liko_min = naudotojas.liko_uzrakinta_min(dabar)
        return _uzrakinta(f"Paskyra laikinai užrakinta. Bandykite dar kartą po {liko_min} min.")

    if not naudotojas.gali_prisijungti(slaptazodis):
        return _nesekmingas_bandymas(naudotojas, dabar)

    naudotojas.uzregistruoti_sekminga(dabar)
    return Response(_zetonai(naudotojas))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def atsijungimas(request):
    """AUT-03: panaikina sesiją (atnaujinimo žetonas įtraukiamas į juodąjį sąrašą)."""
    zetonas = request.data.get("atnaujinimo")
    if zetonas:
        try:
            RefreshToken(zetonas).blacklist()
        except TokenError:
            pass
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def as_pats(request):
    return Response(NaudotojasSerializer(request.user).data)
