from datetime import timedelta

from django.db import migrations, models


def populate_range_end(apps, schema_editor):
    GroceryItem = apps.get_model("planner", "GroceryItem")
    GroceryItemState = apps.get_model("planner", "GroceryItemState")

    for item in GroceryItem.objects.filter(range_end__isnull=True):
        item.range_end = item.week_start + timedelta(days=6)
        item.save(update_fields=["range_end"])

    for state in GroceryItemState.objects.filter(range_end__isnull=True):
        state.range_end = state.week_start + timedelta(days=6)
        state.save(update_fields=["range_end"])


class Migration(migrations.Migration):

    dependencies = [
        ("planner", "0005_ingredient_unit_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="groceryitem",
            name="range_end",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="groceryitemstate",
            name="range_end",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(populate_range_end, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="groceryitem",
            name="range_end",
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name="groceryitemstate",
            name="range_end",
            field=models.DateField(),
        ),
        migrations.RemoveConstraint(
            model_name="groceryitemstate",
            name="unique_grocery_item_state",
        ),
        migrations.AddConstraint(
            model_name="groceryitemstate",
            constraint=models.UniqueConstraint(
                fields=("week_start", "range_end", "ingredient"),
                name="unique_grocery_item_state_range",
            ),
        ),
    ]
