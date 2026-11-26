from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from sales.models import Sale

# FR-07: salės paruošimas po seanso
SALES_PARUOSIMAS = timedelta(minutes=15)


class Zanras(models.Model):
    pavadinimas = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "žanras"
        verbose_name_plural = "žanrai"
        ordering = ["pavadinimas"]

    def __str__(self):
        return self.pavadinimas


class FilmuPlatintojas(models.Model):
    pavadinimas = models.CharField(max_length=100)
    el_pastas = models.EmailField(blank=True)

    class Meta:
        verbose_name = "filmų platintojas"
        verbose_name_plural = "filmų platintojai"
        ordering = ["pavadinimas"]

    def __str__(self):
        return self.pavadinimas


class Filmas(models.Model):
    class Cenzas(models.TextChoices):
        V = "V", "V"
        N7 = "N7", "N-7"
        N13 = "N13", "N-13"
        N16 = "N16", "N-16"
        N18 = "N18", "N-18"

    pavadinimas = models.CharField(max_length=200)
    originalus_pavadinimas = models.CharField(max_length=200, blank=True)
    aprasymas = models.TextField(max_length=2000, blank=True)
    trukme_min = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(400)])
    cenzas = models.CharField(max_length=3, choices=Cenzas.choices)
    premjeros_data = models.DateField(null=True, blank=True)
    kalba = models.CharField(max_length=100, blank=True)
    plakatas = models.ImageField(upload_to="plakatai/", blank=True)
    zanrai = models.ManyToManyField(Zanras, related_name="filmai")
    platintojas = models.ForeignKey(FilmuPlatintojas, on_delete=models.PROTECT, related_name="filmai")

    class Meta:
        verbose_name = "filmas"
        verbose_name_plural = "filmai"
        ordering = ["pavadinimas"]

    def __str__(self):
        return self.pavadinimas


class Seansas(models.Model):
    class Formatas(models.TextChoices):
        F2D = "F2D", "2D"
        F3D = "F3D", "3D"

    class Busena(models.TextChoices):
        SUPLANUOTAS = "SUPLANUOTAS", "Suplanuotas"
        ATSAUKTAS = "ATSAUKTAS", "Atšauktas"

    filmas = models.ForeignKey(Filmas, on_delete=models.PROTECT, related_name="seansai")
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="seansai")
    pradzia = models.DateTimeField()
    pabaiga = models.DateTimeField()
    formatas = models.CharField(max_length=3, choices=Formatas.choices, default=Formatas.F2D)
    busena = models.CharField(max_length=12, choices=Busena.choices, default=Busena.SUPLANUOTAS)

    class Meta:
        verbose_name = "seansas"
        verbose_name_plural = "seansai"
        ordering = ["pradzia"]

    @staticmethod
    def apskaiciuoti_pabaiga(pradzia, trukme_min):
        """FR-07: pabaiga = pradžia + filmo trukmė + 15 min salės paruošimui."""
        return pradzia + timedelta(minutes=trukme_min) + SALES_PARUOSIMAS

    def __str__(self):
        return f"{self.filmas} {self.pradzia:%Y-%m-%d %H:%M}"


class SeansoKaina(models.Model):
    class BilietoTipas(models.TextChoices):
        SUAUGUSIOJO = "SUAUGUSIOJO", "Suaugusiojo"
        STUDENTO = "STUDENTO", "Studento"
        SENJORO = "SENJORO", "Senjoro"

    seansas = models.ForeignKey(Seansas, on_delete=models.CASCADE, related_name="kainos")
    bilieto_tipas = models.CharField(max_length=12, choices=BilietoTipas.choices)
    suma = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(99.99)],
    )

    class Meta:
        verbose_name = "seanso kaina"
        verbose_name_plural = "seanso kainos"
        unique_together = [("seansas", "bilieto_tipas")]

    def __str__(self):
        return f"{self.get_bilieto_tipas_display()}: {self.suma} €"
