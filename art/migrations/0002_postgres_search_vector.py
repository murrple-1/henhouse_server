from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps


def _forward_func_add_search_vectors(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as c:
        c.execute(
            """
            ALTER TABLE art_story ADD COLUMN title_search_vector tsvector GENERATED ALWAYS AS (
                to_tsvector('english', title)
            ) STORED"""
        )
        c.execute(
            """
            CREATE INDEX art_story_title_search_vector_idx ON art_story USING GIN (title_search_vector)"""
        )
        c.execute(
            """
            ALTER TABLE art_chapter ADD COLUMN markdown_search_vector tsvector GENERATED ALWAYS AS (
                to_tsvector('english', markdown)
            ) STORED"""
        )
        c.execute(
            """
            CREATE INDEX art_chapter_markdown_search_vector_idx ON art_chapter USING GIN (markdown_search_vector)"""
        )


def _reverse_func_add_search_vectors(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as c:
        c.execute(
            """
            DROP INDEX IF EXISTS art_story_title_search_vector_idx"""
        )
        c.execute(
            """
            ALTER TABLE art_story DROP COLUMN IF EXISTS title_search_vector"""
        )
        c.execute(
            """
            DROP INDEX IF EXISTS art_chapter_markdown_search_vector_idx"""
        )
        c.execute(
            """
            ALTER TABLE art_chapter DROP COLUMN IF EXISTS markdown_search_vector"""
        )


class Migration(migrations.Migration):
    dependencies = [
        ("art", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            _forward_func_add_search_vectors,
            _reverse_func_add_search_vectors,
        ),
    ]
