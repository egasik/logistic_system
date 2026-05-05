from django.db import migrations, models
from django.utils.text import slugify


def fill_category_slugs(apps, schema_editor):
    Category = apps.get_model("core", "Category")
    for category in Category.objects.all().iterator():
        if category.slug:
            continue
        base = slugify(category.name) or "category"
        category.slug = f"{base}-{category.id}"
        category.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_product_schema_alignment"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.RunPython(fill_category_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(unique=True),
        ),
    ]
