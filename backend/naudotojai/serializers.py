import re

from rest_framework import serializers

from .models import Naudotojas


class NaudotojasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Naudotojas
        fields = ["id", "email", "vardas", "role"]


class RegistracijaSerializer(serializers.Serializer):
    """FR-10: registracijos duomenų tikrinimas serveryje (NFR-06)."""

    vardas = serializers.CharField(min_length=1, max_length=50, error_messages={
        "blank": "Įveskite vardą.", "required": "Įveskite vardą.",
        "max_length": "Vardas negali būti ilgesnis nei 50 simbolių.",
    })
    email = serializers.EmailField(error_messages={
        "invalid": "Įveskite galiojantį el. pašto adresą.",
        "blank": "Įveskite el. paštą.", "required": "Įveskite el. paštą.",
    })
    slaptazodis = serializers.CharField(write_only=True, error_messages={
        "blank": "Įveskite slaptažodį.", "required": "Įveskite slaptažodį.",
    })
    slaptazodis2 = serializers.CharField(write_only=True, error_messages={
        "blank": "Pakartokite slaptažodį.", "required": "Pakartokite slaptažodį.",
    })
    sutikimas = serializers.BooleanField()

    def validate_email(self, reiksme):
        reiksme = reiksme.lower()
        if Naudotojas.objects.filter(email=reiksme).exists():
            raise serializers.ValidationError("Šis el. paštas jau užregistruotas. Prisijunkite.")
        return reiksme

    def validate_slaptazodis(self, reiksme):
        if len(reiksme) < 8 or not re.search(r"[^\W\d_]", reiksme) or not re.search(r"\d", reiksme):
            raise serializers.ValidationError(
                "Slaptažodį turi sudaryti bent 8 simboliai, bent viena raidė ir vienas skaitmuo."
            )
        return reiksme

    def validate_sutikimas(self, reiksme):
        if not reiksme:
            raise serializers.ValidationError("Norėdami užsiregistruoti, sutikite su privatumo politika.")
        return reiksme

    def validate(self, duomenys):
        if duomenys["slaptazodis"] != duomenys["slaptazodis2"]:
            raise serializers.ValidationError({"slaptazodis2": "Slaptažodžiai nesutampa."})
        return duomenys


class PrisijungimasSerializer(serializers.Serializer):
    email = serializers.EmailField(error_messages={"invalid": "Įveskite galiojantį el. pašto adresą."})
    slaptazodis = serializers.CharField(write_only=True)
