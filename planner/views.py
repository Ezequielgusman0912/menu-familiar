from collections import Counter
from datetime import date, timedelta

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import DishForm, MealPlanEntryForm
from .models import Dish, MealPlanEntry


def start_of_week(day):
    return day - timedelta(days=day.weekday())


def grocery_summary(entries):
    counter = Counter()
    for entry in entries:
        for ingredient in entry.dish.ingredient_list():
            counter[ingredient] += 1
    return sorted(counter.items(), key=lambda item: item[0].lower())


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
            if dish_form.is_valid():
                dish_form.save()
                messages.success(request, "Plato guardado.")
                return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
        else:
            meal_form = MealPlanEntryForm(request.POST, prefix="meal")
            dish_form = DishForm(prefix="dish")
            if meal_form.is_valid():
                meal_form.save()
                messages.success(request, "Comida agendada.")
                return redirect(f"{reverse('dashboard')}?week={week_start.isoformat()}")
    else:
        dish_form = DishForm(prefix="dish")
        meal_form = MealPlanEntryForm(
            prefix="meal", initial={"date": today, "meal_type": MealPlanEntry.LUNCH}
        )

    week_days = [week_start + timedelta(days=index) for index in range(7)]
    week_end = week_start + timedelta(days=6)
    entries = (
        MealPlanEntry.objects.select_related("dish")
        .filter(date__range=(week_start, week_end))
        .order_by("date", "meal_type")
    )

    entries_by_slot = {(entry.date, entry.meal_type): entry for entry in entries}
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
        "dish_form": dish_form,
        "meal_form": meal_form,
        "dishes": Dish.objects.all(),
        "grocery_items": grocery_summary(entries),
        "week_start": week_start,
        "week_end": week_end,
        "previous_week": week_start - timedelta(days=7),
        "next_week": week_start + timedelta(days=7),
        "today": today,
    }
    return render(request, "planner/dashboard.html", context)


def healthcheck(request):
    return HttpResponse("ok", content_type="text/plain")
