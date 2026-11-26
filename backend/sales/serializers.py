"""K6 Salių komponentas: salės formos duomenų tikrinimas (SAL-03, SAL-04)."""
from rest_framework import serializers

from .models import NEPRIEINAMA, Vieta


class VietosTipasSerializer(serializers.Serializer):
    eile = serializers.IntegerField(min_value=1)
    vieta = serializers.IntegerField(min_value=1)
    tipas = serializers.ChoiceField(choices=[*Vieta.Tipas.values, NEPRIEINAMA])


class SalesFormaSerializer(serializers.Serializer):
    pavadinimas = serializers.CharField(max_length=50, error_messages={
        "blank": "Įveskite salės pavadinimą.", "required": "Įveskite salės pavadinimą.",
        "max_length": "Pavadinimas negali būti ilgesnis nei 50 simbolių.",
    })
    eiliu = serializers.IntegerField(min_value=1, max_value=30, error_messages={
        "required": "Įveskite eilių skaičių.", "invalid": "Eilių skaičius turi būti nuo 1 iki 30.",
        "min_value": "Eilių skaičius turi būti nuo 1 iki 30.", "max_value": "Eilių skaičius turi būti nuo 1 iki 30.",
    })
    vietu = serializers.IntegerField(min_value=1, max_value=40, error_messages={
        "required": "Įveskite vietų skaičių eilėje.", "invalid": "Vietų skaičius turi būti nuo 1 iki 40.",
        "min_value": "Vietų skaičius turi būti nuo 1 iki 40.", "max_value": "Vietų skaičius turi būti nuo 1 iki 40.",
    })
    vietos = VietosTipasSerializer(many=True, required=False)

    def validate(self, d):
        for v in d.get("vietos", []):
            if v["eile"] > d["eiliu"] or v["vieta"] > d["vietu"]:
                raise serializers.ValidationError({"vietos": "Nurodyta vieta nepatenka į salės schemą."})
        return d
