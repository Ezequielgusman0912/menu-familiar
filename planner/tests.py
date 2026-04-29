from decimal import Decimal
from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Dish, GroceryItem, GroceryItemState, MealPlanEntry


class DishModelTests(TestCase):
    def test_ingredient_list_splits_multiple_formats(self):
        dish = Dish(name="Tarta", ingredients="Huevos, Cebolla\nQueso; Leche")

        self.assertEqual(
            dish.ingredient_list(),
            ["Huevos", "Cebolla", "Queso", "Leche"],
        )

    def test_ingredient_entries_parse_quantities(self):
        dish = Dish(name="Mila", ingredients="Milanesas x3\nPapas x2,5\nTomate")

        self.assertEqual(
            dish.ingredient_entries(),
            [
                {"name": "Milanesas", "quantity": Decimal("3")},
                {"name": "Papas", "quantity": Decimal("2.5")},
                {"name": "Tomate", "quantity": Decimal("1")},
            ],
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

    def test_delete_meal_removes_entry(self):
        dish = Dish.objects.create(name="Tarta", ingredients="Huevos")
        entry = MealPlanEntry.objects.create(
            date=date(2026, 4, 27), meal_type=MealPlanEntry.LUNCH, dish=dish
        )

        response = self.client.post(
            reverse("dashboard") + "?week=2026-04-27",
            {"action": "delete_meal", "entry_id": entry.id},
        )

        self.assertRedirects(response, reverse("dashboard") + "?week=2026-04-27")
        self.assertFalse(MealPlanEntry.objects.filter(pk=entry.id).exists())

    def test_dashboard_shows_ingredient_quantity_sum(self):
        dish = Dish.objects.create(name="Milanesas", ingredients="Papas x3\nTomate")
        MealPlanEntry.objects.create(
            date=date(2026, 4, 27), meal_type=MealPlanEntry.LUNCH, dish=dish
        )

        response = self.client.get(reverse("dashboard"), {"week": "2026-04-27"})

        self.assertContains(response, "Papas")
        self.assertContains(response, "x3")

    def test_add_manual_grocery_item(self):
        response = self.client.post(
            reverse("dashboard") + "?week=2026-04-27",
            {
                "action": "add_grocery_item",
                "grocery-name": "Lavandina",
                "grocery-quantity": "2",
            },
        )

        self.assertRedirects(response, reverse("dashboard") + "?week=2026-04-27")
        self.assertTrue(
            GroceryItem.objects.filter(
                week_start=date(2026, 4, 27), name="Lavandina", quantity="2"
            ).exists()
        )

    def test_toggle_planned_item_marks_checked(self):
        dish = Dish.objects.create(name="Milanesas", ingredients="Papas x3")
        MealPlanEntry.objects.create(
            date=date(2026, 4, 27), meal_type=MealPlanEntry.LUNCH, dish=dish
        )

        response = self.client.post(
            reverse("dashboard") + "?week=2026-04-27",
            {
                "action": "toggle_planned_item",
                "item_name": "Papas",
                "is_checked": "true",
            },
        )

        self.assertRedirects(response, reverse("dashboard") + "?week=2026-04-27")
        self.assertTrue(
            GroceryItemState.objects.get(
                week_start=date(2026, 4, 27), item_name="Papas"
            ).is_checked
        )

    def test_toggle_manual_item_marks_checked(self):
        item = GroceryItem.objects.create(
            week_start=date(2026, 4, 27), name="Jabon", quantity="1"
        )

        response = self.client.post(
            reverse("dashboard") + "?week=2026-04-27",
            {
                "action": "toggle_manual_item",
                "item_id": item.id,
                "is_checked": "true",
            },
        )

        self.assertRedirects(response, reverse("dashboard") + "?week=2026-04-27")
        item.refresh_from_db()
        self.assertTrue(item.is_checked)

    def test_update_planned_item_quantity_creates_override(self):
        dish = Dish.objects.create(name="Milanesas", ingredients="Papas x3")
        MealPlanEntry.objects.create(
            date=date(2026, 4, 27), meal_type=MealPlanEntry.LUNCH, dish=dish
        )

        response = self.client.post(
            reverse("dashboard") + "?week=2026-04-27",
            {
                "action": "update_planned_item_quantity",
                "item_name": "Papas",
                "quantity": "2",
            },
        )

        self.assertRedirects(response, reverse("dashboard") + "?week=2026-04-27")
        self.assertEqual(
            GroceryItemState.objects.get(
                week_start=date(2026, 4, 27), item_name="Papas"
            ).quantity_override,
            "2",
        )

    def test_update_manual_item_changes_name_and_quantity(self):
        item = GroceryItem.objects.create(
            week_start=date(2026, 4, 27), name="Jabon", quantity="1"
        )

        response = self.client.post(
            reverse("dashboard") + "?week=2026-04-27",
            {
                "action": "update_manual_item",
                "item_id": item.id,
                "name": "Detergente",
                "quantity": "2",
            },
        )

        self.assertRedirects(response, reverse("dashboard") + "?week=2026-04-27")
        item.refresh_from_db()
        self.assertEqual(item.name, "Detergente")
        self.assertEqual(item.quantity, "2")

    def test_dishes_page_updates_dish(self):
        dish = Dish.objects.create(name="Milanesa", ingredients="Papas x2", notes="")

        response = self.client.post(
            reverse("dishes"),
            {
                "action": "update_dish",
                "dish_id": dish.id,
                f"dish-{dish.id}-name": "Milanesa napolitana",
                f"dish-{dish.id}-ingredients": "Papas x1\nQueso x1",
                f"dish-{dish.id}-notes": "Cambiar segun semana",
            },
        )

        self.assertRedirects(response, reverse("dishes"))
        dish.refresh_from_db()
        self.assertEqual(dish.name, "Milanesa napolitana")
        self.assertIn("Queso", dish.ingredients)
