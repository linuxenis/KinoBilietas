from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("registracija", views.registracija, name="registracija"),
    path("prisijungimas", views.prisijungimas, name="prisijungimas"),
    path("atsijungimas", views.atsijungimas, name="atsijungimas"),
    path("atnaujinti", TokenRefreshView.as_view(), name="atnaujinti"),
    path("as", views.as_pats, name="as"),
]
