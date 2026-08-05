from django.urls import path

from .views import dashboard, dishes_page, food_items_page, grocery_view, healthcheck

urlpatterns = [
    path("health/", healthcheck, name="healthcheck"),
    path("", dashboard, name="dashboard"),
    path("comidas/", dishes_page, name="dishes"),
    path("items-comidas/", food_items_page, name="food_items"),
    path("super/", grocery_view, name="grocery"),
]
