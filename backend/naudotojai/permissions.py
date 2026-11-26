from rest_framework.permissions import BasePermission


class YraAdministratorius(BasePermission):
    """FR-13 / AUT-04: administravimo funkcijos tik administratoriaus rolei."""

    message = "Neturite teisės atlikti šio veiksmo."

    def has_permission(self, request, view):
        naudotojas = request.user
        return bool(naudotojas and naudotojas.is_authenticated and naudotojas.yra_administratorius)
