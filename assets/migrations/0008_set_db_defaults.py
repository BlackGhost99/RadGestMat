"""Migration to set sensible DB defaults and backfill NULLs for assets_materiel.

This migration sets server-side defaults for timestamps and status fields so
that manual SQL inserts (or tools) that don't provide these fields won't fail.
It also updates existing rows where fields are NULL.

NOTE: Only runs on PostgreSQL. SQLite doesn't require these operations because
Django handles defaults at the application level.
"""
from django.db import migrations, connection


def set_db_defaults(apps, schema_editor):
    """Apply PostgreSQL-specific defaults. Skip on SQLite."""
    if connection.vendor != 'postgresql':
        # SQLite doesn't support ALTER COLUMN SET DEFAULT syntax
        # Django handles defaults at application level, so skipping is safe
        return
    
    with connection.cursor() as cursor:
        cursor.execute("""
            -- Ensure timestamps are set
            UPDATE assets_materiel SET date_creation = now() WHERE date_creation IS NULL;
            UPDATE assets_materiel SET date_modification = now() WHERE date_modification IS NULL;

            -- Ensure status fields have defaults where missing
            UPDATE assets_materiel SET etat_technique = 'FONCTIONNEL' WHERE etat_technique IS NULL OR etat_technique = '';
            UPDATE assets_materiel SET statut_disponibilite = 'DISPONIBLE' WHERE statut_disponibilite IS NULL OR statut_disponibilite = '';

            -- Ensure asset_id has a default value for legacy rows
            UPDATE assets_materiel SET asset_id = 'NEW' WHERE asset_id IS NULL OR asset_id = '';

            -- Set column defaults to avoid failing manual inserts without timestamps
            ALTER TABLE assets_materiel ALTER COLUMN date_creation SET DEFAULT now();
            ALTER TABLE assets_materiel ALTER COLUMN date_modification SET DEFAULT now();
            ALTER TABLE assets_materiel ALTER COLUMN etat_technique SET DEFAULT 'FONCTIONNEL';
            ALTER TABLE assets_materiel ALTER COLUMN statut_disponibilite SET DEFAULT 'DISPONIBLE';
            ALTER TABLE assets_materiel ALTER COLUMN asset_id SET DEFAULT 'NEW';
        """)


def reverse_db_defaults(apps, schema_editor):
    """Reverse the PostgreSQL defaults. Skip on SQLite."""
    if connection.vendor != 'postgresql':
        return
    
    with connection.cursor() as cursor:
        cursor.execute("""
            ALTER TABLE assets_materiel ALTER COLUMN date_creation DROP DEFAULT;
            ALTER TABLE assets_materiel ALTER COLUMN date_modification DROP DEFAULT;
            ALTER TABLE assets_materiel ALTER COLUMN etat_technique DROP DEFAULT;
            ALTER TABLE assets_materiel ALTER COLUMN statut_disponibilite DROP DEFAULT;
            ALTER TABLE assets_materiel ALTER COLUMN asset_id DROP DEFAULT;
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0007_notificationlog_notificationpreferences_and_more'),
    ]

    operations = [
        migrations.RunPython(set_db_defaults, reverse_db_defaults),
    ]

