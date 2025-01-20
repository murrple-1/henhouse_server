# Generated by Django 5.1.4 on 2025-01-20 04:56

import django.db.models.deletion
import django.utils.timezone
import uuid_extensions
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "name",
                    models.CharField(max_length=128, primary_key=True, serialize=False),
                ),
                ("pretty_name", models.CharField(max_length=128)),
                ("description", models.TextField(blank=True, default="")),
            ],
        ),
        migrations.CreateModel(
            name="Chapter",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid_extensions.uuid7,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                ("synopsis", models.CharField(max_length=256)),
                ("index", models.PositiveIntegerField()),
                ("markdown", models.TextField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "name",
                    models.CharField(max_length=128, primary_key=True, serialize=False),
                ),
                ("pretty_name", models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name="ChapterReport",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid_extensions.uuid7,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "kind",
                    models.IntegerField(
                        choices=[(0, "Other"), (1, "Dmca"), (2, "Abuse")]
                    ),
                ),
                ("details", models.CharField(max_length=1024)),
                (
                    "chapter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="art.chapter"
                    ),
                ),
                (
                    "submitter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Story",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid_extensions.uuid7,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("title", models.TextField()),
                ("synopsis", models.CharField(max_length=256)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("is_nsfw", models.BooleanField(default=False)),
                (
                    "category",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="stories",
                        to="art.category",
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stories",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "favorites_of",
                    models.ManyToManyField(
                        blank=True,
                        related_name="favorite_stories",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "tags",
                    models.ManyToManyField(
                        blank=True, related_name="stories", to="art.tag"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="chapter",
            name="story",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chapters",
                to="art.story",
            ),
        ),
        migrations.CreateModel(
            name="StoryReport",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid_extensions.uuid7,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "kind",
                    models.IntegerField(
                        choices=[(0, "Other"), (1, "Dmca"), (2, "Abuse")]
                    ),
                ),
                ("details", models.CharField(max_length=1024)),
                (
                    "story",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="art.story"
                    ),
                ),
                (
                    "submitter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="chapter",
            constraint=models.UniqueConstraint(
                fields=("story", "index"), name="chapter__unique__story__index"
            ),
        ),
    ]
