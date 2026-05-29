from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    DishForm,
    DishIngredientForm,
    GroceryItemForm,
    IngredientForm,
    MealPlanEntryForm,
)
from .models import (
    Dish,
    DishIngredient,
    GroceryItem,
    GroceryItemState,
    Ingredient,
    MealPlanEntry,
)


def start_of_week(day):
    return day - timedelta(days=day.weekday())


def format_quantity(quantity):
    if quantity == quantity.to_integral():
        return str(int(quantity))
    return str(quantity.normalize()).replace(".", ",")


def grocery_summary(entries, week_start):
    counter = {}
    for entry in entries:
        for ingredient in entry.dish.ingredient_entries():
            counter.setdefault(
                ingredient["id"],
                {
                    "name": ingredient["name"],
                    "quantity": Decimal("0"),
                    "unit_label": ingredient["unit_label"],
                },
            )
            counter[ingredient["id"]]["quantity"] += ingredient["quantity"]

    states = {
        state.ingredient_id: state
        for state in GroceryItemState.objects.filter(week_start=week_start)
        if state.ingredient_id
    }
    items = []
    sorted_items = sorted(counter.items(), key=lambda item: item[1]["name"].lower())
    for ingredient_id, item in sorted_items:
        display_quantity = format_quantity(item["quantity"])
        state = states.get(ingredient_id)
        items.append(
            {
                "id": ingredient_id,
                "name": item["name"],
                "quantity": state.quantity_override or display_quantity if state else display_quantity,
                "unit_label": item["unit_label"],
                "is_checked": state.is_checked if state else False,
                "kind": "planned",
            }
        )
    return items


def filtered_ingredients(query):
    if not query:
        return Ingredient.objects.none()
    return Ingredient.objects.filter(name__icontains=query)[:20]


def add_selected_items_to_dish(dish, post_data):
    for ingredient_id in post_data.getlist("ingredient_ids"):
        ingredient = Ingredient.objects.filter(pk=ingredient_id).first()
        if not ingredient:
            continue

        raw_quantity = post_data.get(f"ingredient_quantity_{ingredient_id}", "1")
        raw_quantity = raw_quantity.replace(",", ".").strip() or "1"
        try:
            quantity = Decimal(raw_quantity)
        except Exception:
            quantity = Decimal("1")

        dish_item, created = DishIngredient.objects.get_or_create(
            dish=dish,
            ingredient=ingredient,
            defaults={"quantity": quantity},
        )
        if not created:
            dish_item.quantity += quantity
            dish_item.save(update_fields=["quantity"])


def dashboard(request):
    today = timezone.localdate()
    week_param = request.GET.get("week")
    if week_param:
        selected_day = date.fromisoformat(week_param)
    else:
        selected_day = today

    week_start = start_of_week(selected_day)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_dish":
            dish_form = DishForm(request.POST, prefix="dish")
            meal_form = MealPlanEntryForm(prefix="meal")
            grocery_form = GroceryItemForm(prefix="grocery")
            if dish_form.is_valid():
                dish_form.save()
                messages.success(request, "Plato guardado.")
                return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        elif action == "delete_meal":
            dish_form = DishForm(prefix="dish")
            meal_form = MealPlanEntryForm(prefix="meal")
            grocery_form = GroceryItemForm(prefix="grocery")
            entry_id = request.POST.get("entry_id")
            deleted_count, _ = MealPlanEntry.objects.filter(pk=entry_id).delete()
            if deleted_count:
                messages.success(request, "Comida eliminada.")
            else:
                messages.error(request, "No se encontro la comida para eliminar.")
            return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        elif action == "add_grocery_item":
            dish_form = DishForm(prefix="dish")
            meal_form = MealPlanEntryForm(prefix="meal")
            grocery_form = GroceryItemForm(request.POST, prefix="grocery")
            if grocery_form.is_valid():
                grocery_item = grocery_form.save(commit=False)
                grocery_item.week_start = week_start
                grocery_item.save()
                messages.success(request, "Articulo agregado a la lista.")
                return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        elif action == "update_planned_item_quantity":
            dish_form = DishForm(prefix="dish")
            meal_form = MealPlanEntryForm(prefix="meal")
            grocery_form = GroceryItemForm(prefix="grocery")
            ingredient_id = request.POST.get("ingredient_id")
            quantity = request.POST.get("quantity", "").strip()
            ingredient = Ingredient.objects.filter(pk=ingredient_id).first()
            if ingredient and quantity:
                GroceryItemState.objects.update_or_create(
                    week_start=week_start,
                    ingredient=ingredient,
                    defaults={"quantity_override": quantity},
                )
                messages.success(request, f"Cantidad actualizada para {ingredient.name}.")
            return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        elif action == "toggle_planned_item":
            dish_form = DishForm(prefix="dish")
            meal_form = MealPlanEntryForm(prefix="meal")
            grocery_form = GroceryItemForm(prefix="grocery")
            ingredient_id = request.POST.get("ingredient_id")
            is_checked = request.POST.get("is_checked") == "true"
            ingredient = Ingredient.objects.filter(pk=ingredient_id).first()
            if ingredient:
                state, _ = GroceryItemState.objects.get_or_create(
                    week_start=week_start,
                    ingredient=ingredient,
                )
                state.is_checked = is_checked
                state.save(update_fields=["is_checked"])
            return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        elif action == "toggle_manual_item":
            dish_form = DishForm(prefix="dish")
            meal_form = MealPlanEntryForm(prefix="meal")
            grocery_form = GroceryItemForm(prefix="grocery")
            item_id = request.POST.get("item_id")
            is_checked = request.POST.get("is_checked") == "true"
            GroceryItem.objects.filter(pk=item_id, week_start=week_start).update(
                is_checked=is_checked
            )
            return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        elif action == "update_manual_item":
            dish_form = DishForm(prefix="dish")
            meal_form = MealPlanEntryForm(prefix="meal")
            grocery_form = GroceryItemForm(prefix="grocery")
            item_id = request.POST.get("item_id")
            item = GroceryItem.objects.filter(pk=item_id, week_start=week_start).first()
            if item:
                item.name = request.POST.get("name", item.name).strip() or item.name
                item.quantity = request.POST.get("quantity", item.quantity).strip() or item.quantity
                item.save(update_fields=["name", "quantity"])
                messages.success(request, "Articulo actualizado.")
            return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        elif action == "delete_manual_item":
            dish_form = DishForm(prefix="dish")
            meal_form = MealPlanEntryForm(prefix="meal")
            grocery_form = GroceryItemForm(prefix="grocery")
            item_id = request.POST.get("item_id")
            GroceryItem.objects.filter(pk=item_id, week_start=week_start).delete()
            messages.success(request, "Articulo eliminado de la lista.")
            return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        else:
            meal_form = MealPlanEntryForm(request.POST, prefix="meal")
            dish_form = DishForm(prefix="dish")
            grocery_form = GroceryItemForm(prefix="grocery")
            if meal_form.is_valid():
                meal_form.save()
                messages.success(request, "Comida agendada.")
                return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
    else:
        dish_form = DishForm(prefix="dish")
        meal_form = MealPlanEntryForm(
            prefix="meal", initial={"date": today, "meal_type": MealPlanEntry.LUNCH}
        )
        grocery_form = GroceryItemForm(prefix="grocery", initial={"quantity": "1"})

    week_days = [week_start + timedelta(days=index) for index in range(7)]
    week_end = week_start + timedelta(days=6)
    entries = (
        MealPlanEntry.objects.select_related("dish")
        .prefetch_related("dish__dish_items__ingredient")
        .filter(date__range=(week_start, week_end))
        .order_by("date", "meal_type")
    )

    entries_by_slot = {(entry.date, entry.meal_type): entry for entry in entries}
    manual_grocery_items = GroceryItem.objects.filter(week_start=week_start)
    grocery_items = grocery_summary(entries, week_start)
    rows = []
    for day in week_days:
        rows.append(
            {
                "day": day,
                "almuerzo": entries_by_slot.get((day, MealPlanEntry.LUNCH)),
                "cena": entries_by_slot.get((day, MealPlanEntry.DINNER)),
            }
        )

    context = {
        "rows": rows,
        "meal_form": meal_form,
        "grocery_form": grocery_form,
        "grocery_items": grocery_items,
        "manual_grocery_items": manual_grocery_items,
        "grocery_count": len(grocery_items) + manual_grocery_items.count(),
        "week_start": week_start,
        "week_end": week_end,
        "previous_week": week_start - timedelta(days=7),
        "next_week": week_start + timedelta(days=7),
        "today": today,
    }
    return render(request, "planner/dashboard.html", context)


def dishes_page(request):
    dish_form = DishForm(prefix="dish")
    dish_item_form = DishIngredientForm(prefix="dish-item")
    dish_item_form.fields["ingredient"].queryset = Ingredient.objects.none()
    editing_dish_id = None
    invalid_edit_form = None
    selected_dish_id = request.GET.get("edit")
    dish_query = request.GET.get("dish_q", "").strip()
    create_item_query = request.GET.get("new_item_q", "").strip()
    edit_item_query = request.GET.get("item_q", "").strip()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_dish":
            dish_form = DishForm(request.POST, prefix="dish")
            if dish_form.is_valid():
                created_dish = dish_form.save()
                add_selected_items_to_dish(created_dish, request.POST)
                messages.success(request, "Plato guardado.")
                return redirect(f"{reverse('dishes')}?edit={created_dish.id}")
        elif action == "update_dish":
            dish_id = request.POST.get("dish_id")
            dish = Dish.objects.filter(pk=dish_id).first()
            edit_form = DishForm(request.POST, instance=dish, prefix=f"dish-{dish_id}")
            if dish and edit_form.is_valid():
                edit_form.save()
                add_selected_items_to_dish(dish, request.POST)
                messages.success(request, "Plato actualizado.")
                return redirect(f"{reverse('dishes')}?edit={dish.id}")
            editing_dish_id = int(dish_id) if dish_id and dish_id.isdigit() else None
            selected_dish_id = dish_id
            invalid_edit_form = edit_form
        elif action == "delete_dish":
            dish_id = request.POST.get("dish_id")
            deleted_count, _ = Dish.objects.filter(pk=dish_id).delete()
            if deleted_count:
                messages.success(request, "Plato eliminado.")
            else:
                messages.error(request, "No se encontro el plato.")
            return redirect("dishes")
        elif action == "add_dish_item":
            dish_id = request.POST.get("dish_id")
            dish = Dish.objects.filter(pk=dish_id).first()
            dish_item_form = DishIngredientForm(request.POST, prefix="dish-item")
            dish_item_form.fields["ingredient"].queryset = Ingredient.objects.all()
            if dish and dish_item_form.is_valid():
                dish_item = dish_item_form.save(commit=False)
                dish_item.dish = dish
                existing = DishIngredient.objects.filter(
                    dish=dish, ingredient=dish_item.ingredient
                ).first()
                if existing:
                    existing.quantity += dish_item.quantity
                    existing.save(update_fields=["quantity"])
                else:
                    dish_item.save()
                messages.success(request, "Item agregado al plato.")
                return redirect(f"{reverse('dishes')}?edit={dish.id}")
            selected_dish_id = dish_id
        elif action == "add_selected_dish_items":
            dish_id = request.POST.get("dish_id")
            dish = Dish.objects.filter(pk=dish_id).first()
            if dish:
                add_selected_items_to_dish(dish, request.POST)
                messages.success(request, "Items agregados a la comida.")
                return redirect(f"{reverse('dishes')}?edit={dish.id}")
            selected_dish_id = dish_id
        elif action == "update_dish_item":
            dish_item_id = request.POST.get("dish_item_id")
            dish_item = DishIngredient.objects.select_related("dish").filter(pk=dish_item_id).first()
            quantity = request.POST.get("quantity", "").replace(",", ".").strip()
            if dish_item and quantity:
                dish_item.quantity = Decimal(quantity)
                dish_item.save(update_fields=["quantity"])
                messages.success(request, "Cantidad actualizada.")
                return redirect(f"{reverse('dishes')}?edit={dish_item.dish_id}")
        elif action == "delete_dish_item":
            dish_item_id = request.POST.get("dish_item_id")
            dish_item = DishIngredient.objects.select_related("dish").filter(pk=dish_item_id).first()
            if dish_item:
                dish_id = dish_item.dish_id
                dish_item.delete()
                messages.success(request, "Item quitado del plato.")
                return redirect(f"{reverse('dishes')}?edit={dish_id}")

    dishes = []
    if dish_query:
        dishes = list(
            Dish.objects.filter(name__icontains=dish_query)
            .prefetch_related("dish_items__ingredient")[:20]
        )

    ingredients = []
    if edit_item_query:
        ingredients = list(filtered_ingredients(edit_item_query))

    create_ingredients = []
    if create_item_query:
        create_ingredients = list(filtered_ingredients(create_item_query))

    selected_dish = None
    selected_form = None
    if selected_dish_id and str(selected_dish_id).isdigit():
        selected_dish = (
            Dish.objects.prefetch_related("dish_items__ingredient")
            .filter(pk=selected_dish_id)
            .first()
        )
    if selected_dish:
        selected_form = DishForm(instance=selected_dish, prefix=f"dish-{selected_dish.id}")
        if editing_dish_id == selected_dish.id and invalid_edit_form is not None:
            selected_form = invalid_edit_form
        if edit_item_query:
            dish_item_form.fields["ingredient"].queryset = filtered_ingredients(
                edit_item_query
            )

    context = {
        "dish_form": dish_form,
        "dish_item_form": dish_item_form,
        "create_item_query": create_item_query,
        "create_ingredients": create_ingredients,
        "edit_item_query": edit_item_query,
        "ingredients": ingredients,
        "ingredient_count": Ingredient.objects.count(),
        "dish_query": dish_query,
        "dishes": dishes,
        "dish_count": Dish.objects.count(),
        "dish_options": Dish.objects.order_by("name").values_list("name", flat=True),
        "ingredient_options": Ingredient.objects.order_by("name").values_list(
            "name", flat=True
        ),
        "selected_dish": selected_dish,
        "selected_form": selected_form,
    }
    return render(request, "planner/dishes.html", context)


def food_items_page(request):
    ingredient_form = IngredientForm(prefix="ingredient")
    item_query = request.GET.get("item_q", "").strip()
    selected_ingredient_id = request.GET.get("edit_item")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_ingredient":
            ingredient_form = IngredientForm(request.POST, prefix="ingredient")
            if ingredient_form.is_valid():
                ingredient = ingredient_form.save()
                messages.success(request, "Item guardado.")
                return redirect(f"{reverse('food_items')}?edit_item={ingredient.id}")
        elif action == "update_ingredient":
            ingredient_id = request.POST.get("ingredient_id")
            ingredient = Ingredient.objects.filter(pk=ingredient_id).first()
            edit_item_form = IngredientForm(
                request.POST, instance=ingredient, prefix=f"ingredient-{ingredient_id}"
            )
            if ingredient and edit_item_form.is_valid():
                edit_item_form.save()
                messages.success(request, "Item actualizado.")
                return redirect(f"{reverse('food_items')}?edit_item={ingredient.id}")
        elif action == "delete_ingredient":
            ingredient_id = request.POST.get("ingredient_id")
            ingredient = Ingredient.objects.filter(pk=ingredient_id).first()
            if ingredient:
                try:
                    ingredient.delete()
                    messages.success(request, "Item eliminado.")
                except ProtectedError:
                    messages.error(
                        request,
                        "No se puede eliminar un item que esta usado en un plato.",
                    )
            return redirect("food_items")

    ingredients = []
    if item_query:
        ingredients = list(filtered_ingredients(item_query))

    selected_ingredient = None
    selected_ingredient_form = None
    if selected_ingredient_id and str(selected_ingredient_id).isdigit():
        selected_ingredient = Ingredient.objects.filter(pk=selected_ingredient_id).first()
    if selected_ingredient:
        selected_ingredient_form = IngredientForm(
            instance=selected_ingredient,
            prefix=f"ingredient-{selected_ingredient.id}",
        )

    context = {
        "ingredient_form": ingredient_form,
        "item_query": item_query,
        "ingredients": ingredients,
        "ingredient_count": Ingredient.objects.count(),
        "ingredient_options": Ingredient.objects.order_by("name").values_list(
            "name", flat=True
        ),
        "selected_ingredient": selected_ingredient,
        "selected_ingredient_form": selected_ingredient_form,
    }
    return render(request, "planner/food_items.html", context)


def healthcheck(request):
    return HttpResponse("ok", content_type="text/plain")
