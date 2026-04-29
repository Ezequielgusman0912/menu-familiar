from django.urls import path

from .views import dashboard, dishes_page, healthcheck

urlpatterns = [
    path("health/", healthcheck, name="healthcheck"),
    path("", dashboard, name="dashboard"),
    path("comidas/", dishes_page, name="dishes"),
]
