from decimal import Decimal

from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.normalize_name(self.name)
        super().save(*args, **kwargs)

    @staticmethod
    def normalize_name(name):
        clean_name = " ".join(name.strip().lower().split())
        if len(clean_name) > 3 and clean_name.endswith("s"):
            clean_name = clean_name[:-1]
        return clean_name.capitalize()


class Dish(models.Model):
    name = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def ingredient_entries(self):
        return [
            {
                "id": dish_item.ingredient_id,
                "name": dish_item.ingredient.name,
                "quantity": dish_item.quantity,
            }
            for dish_item in self.dish_items.select_related("ingredient")
        ]


class DishIngredient(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name="dish_items")
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name="dish_items"
    )
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("1"))

    class Meta:
        ordering = ["ingredient__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["dish", "ingredient"], name="unique_ingredient_per_dish"
            )
        ]

    def __str__(self):
        return f"{self.dish.name} - {self.ingredient.name} x{self.quantity}"


class MealPlanEntry(models.Model):
    LUNCH = "almuerzo"
    DINNER = "cena"
    MEAL_TYPES = [
        (LUNCH, "Almuerzo"),
        (DINNER, "Cena"),
    ]

    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name="planned_meals")
    notes = models.CharField(max_length=180, blank=True)

    class Meta:
        ordering = ["date", "meal_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["date", "meal_type"], name="unique_meal_slot_per_day"
            )
        ]

    def __str__(self):
        return f"{self.date} - {self.get_meal_type_display()}: {self.dish.name}"


class GroceryItem(models.Model):
    week_start = models.DateField()
    name = models.CharField(max_length=120)
    quantity = models.CharField(max_length=40, default="1")
    is_checked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_checked", "name"]

    def __str__(self):
        return f"{self.week_start} - {self.name} x{self.quantity}"


class GroceryItemState(models.Model):
    week_start = models.DateField()
    ingredient = models.ForeignKey(
        Ingredient,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="weekly_states",
    )
    item_name = models.CharField(max_length=120, blank=True, default="")
    is_checked = models.BooleanField(default=False)
    quantity_override = models.CharField(max_length=40, blank=True, default="")

    class Meta:
        ordering = ["ingredient__name", "item_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["week_start", "ingredient"], name="unique_grocery_item_state"
            )
        ]

    def __str__(self):
        name = self.ingredient.name if self.ingredient_id else self.item_name
        return f"{self.week_start} - {name}"
