from django import forms

from .models import Dish, DishIngredient, GroceryItem, Ingredient, MealPlanEntry


class DishForm(forms.ModelForm):
    class Meta:
        model = Dish
        fields = ["name", "notes"]
        labels = {
            "name": "Nombre",
            "notes": "Notas",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Milanesas con pure"}),
            "notes": forms.Textarea(attrs={"rows": 2, "placeholder": "Opcional"}),
        }


class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ["name", "unit_type"]
        labels = {
            "name": "Nombre",
            "unit_type": "Se cuenta por",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Papa"}),
        }

    def clean_name(self):
        return Ingredient.normalize_name(self.cleaned_data["name"])


class DishIngredientForm(forms.ModelForm):
    class Meta:
        model = DishIngredient
        fields = ["ingredient", "quantity"]
        labels = {
            "ingredient": "Item",
            "quantity": "Cantidad",
        }
        widgets = {
            "quantity": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01", "placeholder": "Ej. 2"}
            ),
        }


class MealPlanEntryForm(forms.ModelForm):
    class Meta:
        model = MealPlanEntry
        fields = ["date", "meal_type", "dish", "notes"]
        labels = {
            "date": "Fecha",
            "meal_type": "Tipo de comida",
            "dish": "Plato",
            "notes": "Notas",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.TextInput(attrs={"placeholder": "Opcional"}),
        }


class GroceryItemForm(forms.ModelForm):
    class Meta:
        model = GroceryItem
        fields = ["name", "quantity"]
        labels = {
            "name": "Nombre",
            "quantity": "Cantidad",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ej. Lavandina"}),
            "quantity": forms.TextInput(attrs={"placeholder": "Ej. 2 o 1 bidon"}),
        }
