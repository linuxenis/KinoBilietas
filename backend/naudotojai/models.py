from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class NaudotojoValdytojas(BaseUserManager):
    use_in_migrations = True

    def _sukurti(self, email, password, **extra):
        if not email:
            raise ValueError("El. paštas privalomas")
        email = self.normalize_email(email).lower()
        naudotojas = self.model(email=email, **extra)
        naudotojas.set_password(password)
        naudotojas.save(using=self._db)
        return naudotojas

    def create_user(self, email, password=None, **extra):
        extra.setdefault("role", Naudotojas.Role.KLIENTAS)
        return self._sukurti(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("role", Naudotojas.Role.ADMINISTRATORIUS)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self._sukurti(email, password, **extra)


class Naudotojas(AbstractUser):
    """Registruotas naudotojas (2-14 lentelė). Rolė skiria klientą ir administratorių."""

    class Role(models.TextChoices):
        KLIENTAS = "KLIENTAS", "Klientas"
        ADMINISTRATORIUS = "ADMINISTRATORIUS", "Administratorius"

    username = None
    first_name = None
    last_name = None
    email = models.EmailField("el. paštas", unique=True)
    vardas = models.CharField(max_length=50)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.KLIENTAS)
    sukurta = models.DateTimeField(auto_now_add=True)
    nesekmingi_bandymai = models.PositiveSmallIntegerField(default=0)
    uzrakinta_iki = models.DateTimeField(null=True, blank=True)
    # Klientui (NFR-12)
    sutikimas_su_politika = models.BooleanField(default=False)
    sutikimo_data = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["vardas"]

    objects = NaudotojoValdytojas()

    class Meta:
        verbose_name = "naudotojas"
        verbose_name_plural = "naudotojai"

    @property
    def yra_administratorius(self):
        return self.role == self.Role.ADMINISTRATORIUS

    def __str__(self):
        return self.email
