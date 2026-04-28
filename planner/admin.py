from django.contrib import admin

from .models import Dish, MealPlanEntry


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name", "ingredients")


@admin.register(MealPlanEntry)
class MealPlanEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "meal_type", "dish")
    list_filter = ("meal_type", "date")
    search_fields = ("dish__name",)

# Register your models here.
