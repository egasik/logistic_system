from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_brand_schema_alignment"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_admin",
            field=models.BooleanField(default=False),
        ),
    ]
