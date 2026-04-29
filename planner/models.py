import re
from decimal import Decimal, InvalidOperation

from django.db import models


class Dish(models.Model):
    name = models.CharField(max_length=120)
    ingredients = models.TextField(
        help_text="Escribi un ingrediente por linea o separados por coma."
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def ingredient_list(self):
        raw = self.ingredients.replace(";", "\n")
        raw = re.sub(r"(?<!\d),(?!\d)", "\n", raw)
        return [item.strip() for item in raw.splitlines() if item.strip()]

    def ingredient_entries(self):
        entries = []
        for item in self.ingredient_list():
            name, quantity = self.parse_ingredient(item)
            entries.append({"name": name, "quantity": quantity})
        return entries

    @staticmethod
    def parse_ingredient(item):
        match = re.match(r"^(?P<name>.+?)\s*x\s*(?P<quantity>\d+(?:[.,]\d+)?)$", item, re.IGNORECASE)
        if not match:
            return item, Decimal("1")

        name = match.group("name").strip()
        raw_quantity = match.group("quantity").replace(",", ".")
        try:
            quantity = Decimal(raw_quantity)
        except InvalidOperation:
            quantity = Decimal("1")
        return name, quantity


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
    item_name = models.CharField(max_length=120)
    is_checked = models.BooleanField(default=False)
    quantity_override = models.CharField(max_length=40, blank=True, default="")

    class Meta:
        ordering = ["item_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["week_start", "item_name"], name="unique_grocery_item_state"
            )
        ]

    def __str__(self):
        return f"{self.week_start} - {self.item_name}"
