from django.db import migrations


def ensure_user_is_admin_column(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(core_user)")
        columns = {row[1] for row in cursor.fetchall()}
        if "is_admin" not in columns:
            cursor.execute("ALTER TABLE core_user ADD COLUMN is_admin bool NOT NULL DEFAULT 0")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_user_is_admin_alignment"),
    ]

    operations = [
        migrations.RunPython(ensure_user_is_admin_column, migrations.RunPython.noop),
    ]
