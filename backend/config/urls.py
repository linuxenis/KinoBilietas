from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# NFR-03: visi REST API adresai prasideda /api/v1/
urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/v1/auth/", include("naudotojai.urls")),
    path("api/v1/", include("sales.urls")),
    path("api/v1/", include("repertuaras.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
