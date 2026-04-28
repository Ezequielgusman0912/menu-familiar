from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Dish, MealPlanEntry


class DishModelTests(TestCase):
    def test_ingredient_list_splits_multiple_formats(self):
        dish = Dish(name="Tarta", ingredients="Huevos, Cebolla\nQueso; Leche")

        self.assertEqual(
            dish.ingredient_list(),
            ["Huevos", "Cebolla", "Queso", "Leche"],
        )


class DashboardTests(TestCase):
    def test_dashboard_renders_planned_meal(self):
        dish = Dish.objects.create(name="Pasta", ingredients="Fideos\nSalsa")
        MealPlanEntry.objects.create(
            date=date(2026, 4, 27), meal_type=MealPlanEntry.LUNCH, dish=dish
        )

        response = self.client.get(reverse("dashboard"), {"week": "2026-04-27"})

        self.assertContains(response, "Pasta")

    def test_healthcheck_returns_ok(self):
        response = self.client.get(reverse("healthcheck"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
