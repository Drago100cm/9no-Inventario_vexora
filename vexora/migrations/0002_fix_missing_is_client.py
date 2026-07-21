from django.db import migrations


def add_missing_is_client(apps, schema_editor):
    CustomUser = apps.get_model(
        "vexora",
        "CustomUser",
    )

    table_name = CustomUser._meta.db_table
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        description = (
            connection.introspection
            .get_table_description(
                cursor,
                table_name,
            )
        )

        existing_columns = {
            column.name
            for column in description
        }

    # Agregar la columna solamente cuando no exista.
    if "is_client" not in existing_columns:
        field = CustomUser._meta.get_field(
            "is_client"
        )

        schema_editor.add_field(
            CustomUser,
            field,
        )


def reverse_noop(apps, schema_editor):
    # No borrar la columna al regresar la migración.
    pass


class Migration(migrations.Migration):

    # Necesario porque se ejecutará DDL manual en MySQL.
    atomic = False

    dependencies = [
        ("vexora", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            add_missing_is_client,
            reverse_noop,
            atomic=False,
        ),
    ]