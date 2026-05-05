from django.db import migrations


def ensure_user_custom_columns(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(core_user)")
        existing = {row[1] for row in cursor.fetchall()}

        if "phone" not in existing:
            cursor.execute("ALTER TABLE core_user ADD COLUMN phone varchar(32) NULL")
        if "address" not in existing:
            cursor.execute("ALTER TABLE core_user ADD COLUMN address varchar(500) NULL")
        if "is_admin" not in existing:
            cursor.execute("ALTER TABLE core_user ADD COLUMN is_admin bool NOT NULL DEFAULT 0")
        if "is_blocked" not in existing:
            cursor.execute("ALTER TABLE core_user ADD COLUMN is_blocked bool NOT NULL DEFAULT 0")
        if "remember_token" not in existing:
            cursor.execute("ALTER TABLE core_user ADD COLUMN remember_token varchar(100) NULL")


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_ensure_user_is_admin_column"),
    ]

    operations = [
        migrations.RunPython(ensure_user_custom_columns, migrations.RunPython.noop),
    ]
