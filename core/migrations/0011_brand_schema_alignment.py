from django.db import migrations, models
from django.utils import timezone
from django.utils.text import slugify


def fill_brand_slugs(apps, schema_editor):
    Brand = apps.get_model("core", "Brand")

    used = set(
        Brand.objects.exclude(slug__isnull=True)
        .exclude(slug__exact="")
        .values_list("slug", flat=True)
    )

    for brand in Brand.objects.all().iterator():
        if brand.slug:
            continue

        base = slugify(brand.name) or f"brand-{brand.id}"
        slug = base
        idx = 2
        while slug in used:
            slug = f"{base}-{idx}"
            idx += 1

        brand.slug = slug
        brand.save(update_fields=["slug"])
        used.add(slug)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_category_updated_at_alignment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="brand",
            name="name",
            field=models.CharField(max_length=255),
        ),
        migrations.AddField(
            model_name="brand",
            name="created_at",
            field=models.DateTimeField(default=timezone.now),
        ),
        migrations.AddField(
            model_name="brand",
            name="updated_at",
            field=models.DateTimeField(default=timezone.now),
        ),
        migrations.AddField(
            model_name="brand",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.RunPython(fill_brand_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="brand",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="brand",
            name="slug",
            field=models.SlugField(unique=True),
        ),
        migrations.AlterField(
            model_name="brand",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RemoveField(
            model_name="brand",
            name="description",
        ),
        migrations.RemoveField(
            model_name="brand",
            name="is_active",
        ),
    ]
