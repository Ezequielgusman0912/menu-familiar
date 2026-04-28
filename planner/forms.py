from django import forms

from .models import Dish, GroceryItem, MealPlanEntry


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ["name", "ingredients", "notes"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Milanesas con pure"}),
            "ingredients": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Ej. Milanesas x4\nPapas x2\nTomate",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 2, "placeholder": "Opcional"}),
        }


class MealPlanEntryForm(forms.ModelForm):
    class Meta:
        model = MealPlanEntry
        fields = ["date", "meal_type", "dish", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }


class GroceryItemForm(forms.ModelForm):
    class Meta:
        model = GroceryItem
        fields = ["name", "quantity"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Lavandina"}),
            "quantity": forms.TextInput(attrs={"placeholder": "Ej. 2 o 1 bidon"}),
        }
