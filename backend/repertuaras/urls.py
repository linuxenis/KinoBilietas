from django.urls import path

from . import views

urlpatterns = [
    path("seansai", views.repertuaras, name="repertuaras"),
    path("seansai/valdymas", views.seansu_valdymas, name="seansu-valdymas"),
    path("seansai/<int:pk>", views.seansas, name="seansas"),
    path("seansai/<int:pk>/schema", views.seanso_schema, name="seanso-schema"),
    path("seansai/<int:pk>/atsaukti", views.seanso_atsaukimas, name="seanso-atsaukimas"),
    path("zanrai", views.zanrai, name="zanrai"),
    path("platintojai", views.platintojai, name="platintojai"),
    path("filmai", views.filmai, name="filmai"),
    path("filmai/<int:pk>", views.filmas, name="filmas"),
]
