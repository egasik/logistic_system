from django.db import migrations, models
from django.utils.text import slugify


def fill_product_slugs(apps, schema_editor):
    Product = apps.get_model("core", "Product")
    for product in Product.objects.all().iterator():
        if product.slug:
            continue
        base = slugify(product.name) or "product"
        product.slug = f"{base}-{product.id}"
        product.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_brand_stockmovement_and_flags"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="sku",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="product",
            name="stock",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(fill_product_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.SlugField(unique=True),
        ),
    ]
