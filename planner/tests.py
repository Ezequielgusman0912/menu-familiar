from decimal import Decimal
from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Dish, DishIngredient, GroceryItem, GroceryItemState, Ingredient, MealPlanEntry


class DishModelTests(TestCase):
    def test_ingredient_entries_use_saved_items(self):
        dish = Dish.objects.create(name="Tarta")
        huevos = Ingredient.objects.create(name="Huevos")
        queso = Ingredient.objects.create(name="Queso")
        DishIngredient.objects.create(dish=dish, ingredient=huevos, quantity=2)
        DishIngredient.objects.create(dish=dish, ingredient=queso, quantity=1)

        entries = dish.ingredient_entries()

        self.assertEqual(
            entries,
            [
                {"id": huevos.id, "name": "Huevo", "quantity": Decimal("2")},
                {"id": queso.id, "name": "Queso", "quantity": Decimal("1")},
            ],
        )

    def test_ingredient_name_is_normalized_to_singular(self):
        ingredient = Ingredient.objects.create(name="  papas  ")

        self.assertEqual(ingredient.name, "Papa")


class DashboardTests(TestCase):
    def test_dashboard_renders_planned_meal(self):
        dish = Dish.objects.create(name="Pasta")
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
        dish = Dish.objects.create(name="Tarta")
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
        dish = Dish.objects.create(name="Milanesas")
        papa = Ingredient.objects.create(name="Papas")
        DishIngredient.objects.create(dish=dish, ingredient=papa, quantity=3)
        MealPlanEntry.objects.create(
            date=date(2026, 4, 27), meal_type=MealPlanEntry.LUNCH, dish=dish
        )

        response = self.client.get(reverse("dashboard"), {"week": "2026-04-27"})

        self.assertContains(response, "Papa")
        self.assertContains(response, 'value="3"')

    def test_dashboard_sums_same_item_across_dishes(self):
        papa = Ingredient.objects.create(name="Papa")
        first = Dish.objects.create(name="Milanesas")
        second = Dish.objects.create(name="Pastel")
        DishIngredient.objects.create(dish=first, ingredient=papa, quantity=2)
        DishIngredient.objects.create(dish=second, ingredient=papa, quantity=3)
        MealPlanEntry.objects.create(
            date=date(2026, 4, 27), meal_type=MealPlanEntry.LUNCH, dish=first
        )
        MealPlanEntry.objects.create(
            date=date(2026, 4, 28), meal_type=MealPlanEntry.LUNCH, dish=second
        )

        response = self.client.get(reverse("dashboard"), {"week": "2026-04-27"})

        self.assertContains(response, "Papa")
        self.assertContains(response, 'value="5"')

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
        dish = Dish.objects.create(name="Milanesas")
        papa = Ingredient.objects.create(name="Papas")
        DishIngredient.objects.create(dish=dish, ingredient=papa, quantity=3)
        MealPlanEntry.objects.create(
            date=date(2026, 4, 27), meal_type=MealPlanEntry.LUNCH, dish=dish
        )

        response = self.client.post(
            reverse("dashboard") + "?week=2026-04-27",
            {
                "action": "toggle_planned_item",
                "ingredient_id": papa.id,
                "is_checked": "true",
            },
        )

        self.assertRedirects(response, reverse("dashboard") + "?week=2026-04-27")
        self.assertTrue(
            GroceryItemState.objects.get(
                week_start=date(2026, 4, 27), ingredient=papa
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
        dish = Dish.objects.create(name="Milanesas")
        papa = Ingredient.objects.create(name="Papas")
        DishIngredient.objects.create(dish=dish, ingredient=papa, quantity=3)
        MealPlanEntry.objects.create(
            date=date(2026, 4, 27), meal_type=MealPlanEntry.LUNCH, dish=dish
        )

        response = self.client.post(
            reverse("dashboard") + "?week=2026-04-27",
            {
                "action": "update_planned_item_quantity",
                "ingredient_id": papa.id,
                "quantity": "2",
            },
        )

        self.assertRedirects(response, reverse("dashboard") + "?week=2026-04-27")
        self.assertEqual(
            GroceryItemState.objects.get(
                week_start=date(2026, 4, 27), ingredient=papa
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
        dish = Dish.objects.create(name="Milanesa", notes="")

        response = self.client.post(
            reverse("dishes") + f"?edit={dish.id}",
            {
                "action": "update_dish",
                "dish_id": dish.id,
                f"dish-{dish.id}-name": "Milanesa napolitana",
                f"dish-{dish.id}-notes": "Cambiar segun semana",
            },
        )

        self.assertRedirects(response, reverse("dishes") + f"?edit={dish.id}")
        dish.refresh_from_db()
        self.assertEqual(dish.name, "Milanesa napolitana")
        self.assertEqual(dish.notes, "Cambiar segun semana")

    def test_dishes_page_shows_editor_only_for_selected_dish(self):
        first = Dish.objects.create(name="Milanesa", notes="")
        second = Dish.objects.create(name="Pizza", notes="")

        response = self.client.get(reverse("dishes"), {"edit": second.id})

        self.assertContains(response, 'Editor del plato')
        self.assertContains(response, 'Pizza')
        self.assertContains(response, f'dish-{second.id}-name')
        self.assertNotContains(response, f'dish-{first.id}-name')

    def test_dishes_page_does_not_list_dishes_without_filter(self):
        Dish.objects.create(name="Milanesa", notes="")

        response = self.client.get(reverse("dishes"))

        self.assertContains(response, "Usa el filtro para traer platos.")
        self.assertNotContains(response, 'class="dish-selector')

    def test_dishes_page_filters_dishes_and_items(self):
        Dish.objects.create(name="Milanesa", notes="")
        Dish.objects.create(name="Pizza", notes="")
        Ingredient.objects.create(name="Papas")
        Ingredient.objects.create(name="Tomate")

        response = self.client.get(
            reverse("dishes"), {"dish_q": "mila", "item_q": "papa"}
        )

        self.assertContains(response, "Milanesa")
        self.assertNotContains(response, "Pizza")
        self.assertContains(response, "Papa")
        self.assertNotContains(response, "Tomate")

    def test_dishes_page_adds_item_to_dish(self):
        dish = Dish.objects.create(name="Milanesa")
        papa = Ingredient.objects.create(name="Papas")

        response = self.client.post(
            reverse("dishes") + f"?edit={dish.id}",
            {
                "action": "add_dish_item",
                "dish_id": dish.id,
                "dish-item-ingredient": papa.id,
                "dish-item-quantity": "2",
            },
        )

        self.assertRedirects(response, reverse("dishes") + f"?edit={dish.id}")
        self.assertTrue(
            DishIngredient.objects.filter(
                dish=dish, ingredient=papa, quantity=Decimal("2")
            ).exists()
        )
