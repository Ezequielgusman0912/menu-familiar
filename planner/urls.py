from django.urls import path

from .views import dashboard, healthcheck

urlpatterns = [
    path("health/", healthcheck, name="healthcheck"),
    path("", dashboard, name="dashboard"),
]
