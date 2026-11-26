from django.db import models


class KinoTeatras(models.Model):
    pavadinimas = models.CharField(max_length=100)
    adresas = models.CharField(max_length=200, blank=True)
    telefonas = models.CharField(max_length=30, blank=True)
    el_pastas = models.EmailField(blank=True)

    class Meta:
        verbose_name = "kino teatras"
        verbose_name_plural = "kino teatrai"

    def __str__(self):
        return self.pavadinimas


class Sale(models.Model):
    """Salė: struktūros klasė, kurią sudaro eilės (2-14 lentelė)."""

    kino_teatras = models.ForeignKey(KinoTeatras, on_delete=models.CASCADE, related_name="sales")
    pavadinimas = models.CharField(max_length=50)

    class Meta:
        verbose_name = "salė"
        verbose_name_plural = "salės"
        ordering = ["pavadinimas"]

    @property
    def talpa(self):
        """Išvestinis atributas: prieinamų vietų skaičius."""
        return Vieta.objects.filter(eile__sale=self, prieinama=True).count()

    def __str__(self):
        return self.pavadinimas


class Eile(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="eiles")
    numeris = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = "eilė"
        verbose_name_plural = "eilės"
        ordering = ["numeris"]
        unique_together = [("sale", "numeris")]

    def __str__(self):
        return f"{self.sale} {self.numeris} eilė"


class Vieta(models.Model):
    class Tipas(models.TextChoices):
        STANDARTINE = "STANDARTINE", "Standartinė"
        NEIGALIESIEMS = "NEIGALIESIEMS", "Neįgaliesiems"

    eile = models.ForeignKey(Eile, on_delete=models.CASCADE, related_name="vietos")
    numeris = models.PositiveSmallIntegerField()
    tipas = models.CharField(max_length=20, choices=Tipas.choices, default=Tipas.STANDARTINE)
    prieinama = models.BooleanField(default=True)

    class Meta:
        verbose_name = "vieta"
        verbose_name_plural = "vietos"
        ordering = ["numeris"]
        unique_together = [("eile", "numeris")]

    def __str__(self):
        return f"{self.eile}, {self.numeris} vieta"
