from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import DishForm, GroceryItemForm, MealPlanEntryForm
from .models import Dish, GroceryItem, GroceryItemState, MealPlanEntry


def start_of_week(day):
    return day - timedelta(days=day.weekday())


def grocery_summary(entries, week_start):
    counter = {}
    for entry in entries:
        for ingredient in entry.dish.ingredient_entries():
            counter.setdefault(ingredient["name"], Decimal("0"))
            counter[ingredient["name"]] += ingredient["quantity"]

    states = {
        state.item_name: state
        for state in GroceryItemState.objects.filter(week_start=week_start)
    }
    items = []
    for name, quantity in sorted(counter.items(), key=lambda item: item[0].lower()):
        if quantity == quantity.to_integral():
            display_quantity = str(int(quantity))
        else:
            display_quantity = str(quantity.normalize()).replace(".", ",")
        state = states.get(name)
        items.append(
            {
                "name": name,
                "quantity": state.quantity_override or display_quantity if state else display_quantity,
                "is_checked": state.is_checked if state else False,
                "kind": "planned",
            }
        )
    return items


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
            item_name = request.POST.get("item_name", "").strip()
            quantity = request.POST.get("quantity", "").strip()
            if item_name and quantity:
                GroceryItemState.objects.update_or_create(
                    week_start=week_start,
                    item_name=item_name,
                    defaults={"quantity_override": quantity},
                )
                messages.success(request, f"Cantidad actualizada para {item_name}.")
            return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        elif action == "toggle_planned_item":
            dish_form = DishForm(prefix="dish")
            meal_form = MealPlanEntryForm(prefix="meal")
            grocery_form = GroceryItemForm(prefix="grocery")
            item_name = request.POST.get("item_name", "").strip()
            is_checked = request.POST.get("is_checked") == "true"
            if item_name:
                state, _ = GroceryItemState.objects.get_or_create(
                    week_start=week_start,
                    item_name=item_name,
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
    editing_dish_id = None
    invalid_edit_form = None
    selected_dish_id = request.GET.get("edit")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_dish":
            dish_form = DishForm(request.POST, prefix="dish")
            if dish_form.is_valid():
                created_dish = dish_form.save()
                messages.success(request, "Plato guardado.")
                return redirect(f"{reverse('dishes')}?edit={created_dish.id}")
        elif action == "update_dish":
            dish_id = request.POST.get("dish_id")
            dish = Dish.objects.filter(pk=dish_id).first()
            edit_form = DishForm(request.POST, instance=dish, prefix=f"dish-{dish_id}")
            if dish and edit_form.is_valid():
                edit_form.save()
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

    dishes = list(Dish.objects.all())
    selected_dish = None
    selected_form = None
    if selected_dish_id and str(selected_dish_id).isdigit():
        selected_dish = Dish.objects.filter(pk=selected_dish_id).first()
    if selected_dish:
        selected_form = DishForm(instance=selected_dish, prefix=f"dish-{selected_dish.id}")
        if editing_dish_id == selected_dish.id and invalid_edit_form is not None:
            selected_form = invalid_edit_form

    context = {
        "dish_form": dish_form,
        "dishes": dishes,
        "selected_dish": selected_dish,
        "selected_form": selected_form,
    }
    return render(request, "planner/dishes.html", context)


def healthcheck(request):
    return HttpResponse("ok", content_type="text/plain")
