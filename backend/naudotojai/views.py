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


@api_view(["POST"])
@permission_classes([AllowAny])
def prisijungimas(request):
    """API-06 / AUT-02: tikrina duomenis, po 5 nesėkmingų bandymų užrakina 15 min."""
    s = PrisijungimasSerializer(data=request.data)
    s.is_valid(raise_exception=True)
    email = s.validated_data["email"].lower()
    slaptazodis = s.validated_data["slaptazodis"]
    bendra_klaida = {"klaida": "Neteisingas el. paštas arba slaptažodis."}

    naudotojas = Naudotojas.objects.filter(email=email).first()
    if naudotojas is None:
        return Response(bendra_klaida, status=status.HTTP_401_UNAUTHORIZED)

    dabar = timezone.now()
    if naudotojas.uzrakinta_iki and naudotojas.uzrakinta_iki > dabar:
        liko_min = int((naudotojas.uzrakinta_iki - dabar).total_seconds() // 60) + 1
        return Response(
            {"klaida": f"Paskyra laikinai užrakinta. Bandykite dar kartą po {liko_min} min.", "uzrakinta": True},
            status=status.HTTP_423_LOCKED,
        )

    if not naudotojas.check_password(slaptazodis) or not naudotojas.is_active:
        naudotojas.nesekmingi_bandymai += 1
        riba = settings.PRISIJUNGIMO_BANDYMAI
        if naudotojas.nesekmingi_bandymai >= riba:
            naudotojas.uzrakinta_iki = dabar + settings.UZRAKINIMO_TRUKME
            naudotojas.nesekmingi_bandymai = 0
            naudotojas.save(update_fields=["nesekmingi_bandymai", "uzrakinta_iki"])
            minutes = int(settings.UZRAKINIMO_TRUKME.total_seconds() // 60)
            return Response(
                {"klaida": f"Paskyra laikinai užrakinta {minutes} min. po {riba} nesėkmingų bandymų.", "uzrakinta": True},
                status=status.HTTP_423_LOCKED,
            )
        naudotojas.save(update_fields=["nesekmingi_bandymai"])
        liko = riba - naudotojas.nesekmingi_bandymai
        return Response(
            {"klaida": f"Neteisingas el. paštas arba slaptažodis. Liko {liko} bandym{'as' if liko == 1 else 'ai'}."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    naudotojas.nesekmingi_bandymai = 0
    naudotojas.uzrakinta_iki = None
    naudotojas.last_login = dabar
    naudotojas.save(update_fields=["nesekmingi_bandymai", "uzrakinta_iki", "last_login"])
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
