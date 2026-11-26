from django.contrib import admin

from .models import Filmas, FilmuPlatintojas, Seansas, SeansoKaina, Zanras


class SeansoKainaInline(admin.TabularInline):
    model = SeansoKaina
    extra = 0


@admin.register(Seansas)
class SeansasAdmin(admin.ModelAdmin):
    list_display = ("filmas", "sale", "pradzia", "pabaiga", "busena")
    list_filter = ("busena", "sale")
    inlines = [SeansoKainaInline]


admin.site.register(Zanras)
admin.site.register(FilmuPlatintojas)
admin.site.register(Filmas)
