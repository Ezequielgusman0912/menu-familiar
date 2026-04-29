from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("planner", "0002_groceryitem_groceryitemstate"),
    ]

    operations = [
        migrations.AddField(
            model_name="groceryitemstate",
            name="quantity_override",
            field=models.CharField(blank=True, default="", max_length=40),
        ),
    ]
