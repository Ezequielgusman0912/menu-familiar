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
        raw = self.ingredients.replace(";", "\n").replace(",", "\n")
        return [item.strip() for item in raw.splitlines() if item.strip()]


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
