"""
One-off repair: adds any column that a model declares but the live sqlite
table is missing, using Django's own schema editor (same code path as a
real AddField migration) so types/defaults/NOT NULL handling are correct.

Run on the production server with:
    python manage.py shell < fix_missing_columns.py

Root cause: eduweb/migrations/0001_initial.py was edited in place after it
was already applied on this database, instead of adding a new migration.
django_migrations still has "eduweb.0001_initial" recorded as applied, so
`python manage.py migrate` skips it and never notices the new columns.
This script closes that gap directly against the live schema.

Delete this file (and find_missing_columns.py) once you've confirmed the
site is healthy -- these are one-off repair scripts, not part of the app.
"""
from django.apps import apps
from django.db import connection

fixed = []

with connection.cursor() as cursor:
    existing_tables = set(connection.introspection.table_names(cursor))

for model in apps.get_models():
    table = model._meta.db_table
    if table not in existing_tables:
        continue  # whole table missing is a separate problem -- not handled here

    with connection.cursor() as cursor:
        actual_columns = {
            col.name for col in connection.introspection.get_table_description(cursor, table)
        }

    for field in model._meta.local_fields:
        if field.column in actual_columns:
            continue
        with connection.schema_editor() as schema_editor:
            schema_editor.add_field(model, field)
        fixed.append(f"{table}.{field.column}")
        print(f"added: {table}.{field.column}")

print(f"\nDone. Added {len(fixed)} column(s).")
