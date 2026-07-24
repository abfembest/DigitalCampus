"""
One-off diagnostic: compares Django model fields against the actual live
sqlite schema and prints ALTER TABLE statements for any missing columns.

Run on the production server with:
    python manage.py shell < find_missing_columns.py

Caused by eduweb/migrations/0001_initial.py being edited in place (commit
a44b993) after it was already applied on production, instead of adding a
new migration -- so django_migrations thinks 0001_initial is applied and
the new columns were never actually created on the live table.
"""
from django.apps import apps
from django.db import connection

with connection.cursor() as cursor:
    existing_tables = set(connection.introspection.table_names(cursor))

    for model in apps.get_models():
        table = model._meta.db_table
        if table not in existing_tables:
            continue  # whole table missing is a separate, bigger problem

        actual_columns = {
            col.name for col in connection.introspection.get_table_description(cursor, table)
        }

        for field in model._meta.local_fields:
            if field.column not in actual_columns:
                print(f"-- MISSING: {table}.{field.column}  (model: {model.__name__}, field: {field.name})")
                sql, params = field.db_parameters(connection=connection), None
                print(f"   type hint: {field.db_type(connection)}  null={field.null}")
