from django.conf import settings
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

    # --- Paskyros užrakinimas po nesėkmingų prisijungimų (AUT-02) ---

    def yra_uzrakintas(self, dabar):
        return bool(self.uzrakinta_iki and self.uzrakinta_iki > dabar)

    def liko_uzrakinta_min(self, dabar):
        """Likusios užrakinimo minutės, suapvalintos į viršų (rodoma naudotojui)."""
        return int((self.uzrakinta_iki - dabar).total_seconds() // 60) + 1

    def gali_prisijungti(self, slaptazodis):
        return self.check_password(slaptazodis) and self.is_active

    def uzregistruoti_nesekminga(self, dabar):
        """Padidina nesėkmių skaitiklį; pasiekus ribą užrakina paskyrą. Grąžina True, jei užrakinta."""
        self.nesekmingi_bandymai += 1
        if self.nesekmingi_bandymai >= settings.PRISIJUNGIMO_BANDYMAI:
            self.uzrakinta_iki = dabar + settings.UZRAKINIMO_TRUKME
            self.nesekmingi_bandymai = 0
            self.save(update_fields=["nesekmingi_bandymai", "uzrakinta_iki"])
            return True
        self.save(update_fields=["nesekmingi_bandymai"])
        return False

    def uzregistruoti_sekminga(self, dabar):
        self.nesekmingi_bandymai = 0
        self.uzrakinta_iki = None
        self.last_login = dabar
        self.save(update_fields=["nesekmingi_bandymai", "uzrakinta_iki", "last_login"])

    def __str__(self):
        return self.email
