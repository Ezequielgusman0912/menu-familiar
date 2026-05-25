from django.contrib import admin

from .models import Dish, DishIngredient, Ingredient, MealPlanEntry


class DishIngredientInline(admin.TabularInline):
    model = DishIngredient
    extra = 1


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name", "dish_items__ingredient__name")
    inlines = [DishIngredientInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(MealPlanEntry)
class MealPlanEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "meal_type", "dish")
    list_filter = ("meal_type", "date")
    search_fields = ("dish__name",)

# Register your models here.
