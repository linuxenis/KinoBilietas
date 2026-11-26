from django.contrib import admin

from .models import Naudotojas


@admin.register(Naudotojas)
class NaudotojasAdmin(admin.ModelAdmin):
    list_display = ("email", "vardas", "role", "sukurta")
    list_filter = ("role",)
    search_fields = ("email", "vardas")
