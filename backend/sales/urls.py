from django.urls import path

from . import views

urlpatterns = [
    path("kino-teatras", views.kino_teatras, name="kino-teatras"),
    path("sales", views.saliu_sarasas, name="saliu-sarasas"),
    path("sales/<int:pk>", views.sale, name="sale"),
    path("seansai/<int:pk>/schema", views.seanso_schema, name="seanso-schema"),
]
