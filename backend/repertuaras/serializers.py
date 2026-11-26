from decimal import Decimal

from rest_framework import serializers

from sales.models import Sale

from .models import Filmas, FilmuPlatintojas, Seansas, Zanras

_KAINOS_KLAIDOS = {
    "invalid": "Kaina turi būti skaičius.",
    "min_value": "Kaina turi būti nuo 0,01 iki 99,99 €.",
    "max_value": "Kaina turi būti nuo 0,01 iki 99,99 €.",
    "max_decimal_places": "Kaina gali turėti ne daugiau kaip 2 skaitmenis po kablelio.",
    "max_digits": "Kaina turi būti nuo 0,01 iki 99,99 €.",
}


def _kainos_laukas(privalomas):
    klaidos = dict(_KAINOS_KLAIDOS, required="Įveskite suaugusiojo bilieto kainą.", null="Įveskite suaugusiojo bilieto kainą.")
    return serializers.DecimalField(
        max_digits=4, decimal_places=2, min_value=Decimal("0.01"), max_value=Decimal("99.99"),
        required=privalomas, allow_null=not privalomas, error_messages=klaidos,
    )


class SeansoFormaSerializer(serializers.Serializer):
    """FR-07: seanso formos duomenys (2.15 pav.)."""

    filmas = serializers.PrimaryKeyRelatedField(queryset=Filmas.objects.all(), error_messages={
        "required": "Pasirinkite filmą.", "null": "Pasirinkite filmą.", "does_not_exist": "Pasirinkite filmą.",
        "incorrect_type": "Pasirinkite filmą.",
    })
    sale = serializers.PrimaryKeyRelatedField(queryset=Sale.objects.all(), error_messages={
        "required": "Pasirinkite salę.", "null": "Pasirinkite salę.", "does_not_exist": "Pasirinkite salę.",
        "incorrect_type": "Pasirinkite salę.",
    })
    data = serializers.DateField(error_messages={"required": "Pasirinkite datą.", "invalid": "Pasirinkite datą."})
    pradzia = serializers.TimeField(format="%H:%M", error_messages={
        "required": "Įveskite pradžios laiką.", "invalid": "Laikas turi būti formatu VV:MM.",
    })
    formatas = serializers.ChoiceField(choices=Seansas.Formatas.choices, default=Seansas.Formatas.F2D)
    kaina_suaugusiojo = _kainos_laukas(True)
    kaina_studento = _kainos_laukas(False)
    kaina_senjoro = _kainos_laukas(False)


def seanso_administravimui(s):
    kainos = {k.bilieto_tipas: str(k.suma) for k in s.kainos.all()}
    return {
        "id": s.id,
        "filmas": s.filmas_id,
        "filmo_pavadinimas": s.filmas.pavadinimas,
        "sale": s.sale_id,
        "sales_pavadinimas": s.sale.pavadinimas,
        "pradzia": s.pradzia,
        "pabaiga": s.pabaiga,
        "formatas": s.formatas,
        "busena": s.busena,
        "kaina_suaugusiojo": kainos.get("SUAUGUSIOJO"),
        "kaina_studento": kainos.get("STUDENTO"),
        "kaina_senjoro": kainos.get("SENJORO"),
    }


class FilmoFormaSerializer(serializers.ModelSerializer):
    """FR-06 / REP-04: filmo duomenų tikrinimas serveryje (NFR-06)."""

    pavadinimas = serializers.CharField(max_length=200, error_messages={
        "blank": "Įveskite filmo pavadinimą.", "required": "Įveskite filmo pavadinimą.",
        "max_length": "Pavadinimas negali būti ilgesnis nei 200 simbolių.",
    })
    trukme_min = serializers.IntegerField(min_value=1, max_value=400, error_messages={
        "required": "Įveskite filmo trukmę.", "invalid": "Trukmė turi būti skaičius.",
        "min_value": "Trukmė turi būti nuo 1 iki 400 min.", "max_value": "Trukmė turi būti nuo 1 iki 400 min.",
    })
    cenzas = serializers.ChoiceField(choices=Filmas.Cenzas.choices, error_messages={
        "required": "Pasirinkite amžiaus cenzą.", "invalid_choice": "Pasirinkite amžiaus cenzą.",
    })
    zanrai = serializers.PrimaryKeyRelatedField(many=True, queryset=Zanras.objects.all(), error_messages={
        "required": "Pasirinkite bent vieną žanrą.",
    })
    platintojas = serializers.PrimaryKeyRelatedField(queryset=FilmuPlatintojas.objects.all(), error_messages={
        "required": "Pasirinkite platintoją.", "null": "Pasirinkite platintoją.",
        "does_not_exist": "Pasirinkite platintoją.", "incorrect_type": "Pasirinkite platintoją.",
    })
    aprasymas = serializers.CharField(max_length=2000, required=False, allow_blank=True, error_messages={
        "max_length": "Aprašymas negali būti ilgesnis nei 2000 simbolių.",
    })

    class Meta:
        model = Filmas
        fields = [
            "id", "pavadinimas", "originalus_pavadinimas", "aprasymas", "trukme_min", "cenzas",
            "zanrai", "kalba", "premjeros_data", "platintojas", "plakatas",
        ]

    def validate_zanrai(self, reiksme):
        if not reiksme:
            raise serializers.ValidationError("Pasirinkite bent vieną žanrą.")
        return reiksme

    def validate_plakatas(self, failas):
        if failas:
            if failas.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Plakatas negali būti didesnis nei 2 MB.")
            if not failas.name.lower().endswith((".jpg", ".jpeg", ".png")):
                raise serializers.ValidationError("Plakatas turi būti JPG arba PNG formato.")
        return failas


class RepertuaroFilmasSerializer(serializers.ModelSerializer):
    """FR-01: filmo kortelė repertuare."""

    zanrai = serializers.SlugRelatedField(many=True, read_only=True, slug_field="pavadinimas")
    cenzas_rodomas = serializers.CharField(source="get_cenzas_display", read_only=True)

    class Meta:
        model = Filmas
        fields = ["id", "pavadinimas", "trukme_min", "cenzas", "cenzas_rodomas", "zanrai", "plakatas"]


class FilmoInformacijaSerializer(serializers.ModelSerializer):
    """FR-03: visa filmo informacija."""

    zanrai = serializers.SlugRelatedField(many=True, read_only=True, slug_field="pavadinimas")
    cenzas_rodomas = serializers.CharField(source="get_cenzas_display", read_only=True)

    class Meta:
        model = Filmas
        fields = [
            "id", "pavadinimas", "originalus_pavadinimas", "aprasymas", "trukme_min", "cenzas",
            "cenzas_rodomas", "zanrai", "kalba", "premjeros_data", "plakatas",
        ]


def seanso_eilute(seansas, laisvos):
    """FR-01: seanso mygtukas: pradžia, salė, formatas, mažiausia kaina, laisvos vietos."""
    kainos = [k.suma for k in seansas.kainos.all()]
    return {
        "id": seansas.id,
        "pradzia": seansas.pradzia,
        "sale": seansas.sale.pavadinimas,
        "sale_id": seansas.sale_id,
        "formatas": seansas.formatas,
        "maziausia_kaina": str(min(kainos)) if kainos else None,
        "laisvos_vietos": laisvos.get(seansas.sale_id, 0),
    }
