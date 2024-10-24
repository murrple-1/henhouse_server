# TODO replace with regular `uuid` module when finalized in Python
import uuid_extensions
from django.conf import settings
from django.db import connection, models
from django.utils import timezone


class Story(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid_extensions.uuid7)
    title = models.TextField()
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="stories", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(default=timezone.now)
    published_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField("Tag", related_name="stories", blank=True)

    @staticmethod
    def annotate_search_vectors(
        qs: models.QuerySet["Story"],
    ) -> models.QuerySet["Story"]:
        if connection.vendor == "postgresql":  # pragma: no cover
            from django.contrib.postgres.search import SearchVector

            qs = qs.annotate(
                title_search_vector=SearchVector("title"),
            )
        return qs


class Chapter(models.Model):
    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("story", "index"), name="chapter__unique__story__index"
            ),
        )

    uuid = models.UUIDField(primary_key=True, default=uuid_extensions.uuid7)
    story = models.ForeignKey(Story, related_name="chapters", on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    index = models.PositiveIntegerField()
    markdown = models.TextField()

    @staticmethod
    def annotate_search_vectors(
        qs: models.QuerySet["Chapter"],
    ) -> models.QuerySet["Chapter"]:
        if connection.vendor == "postgresql":  # pragma: no cover
            from django.contrib.postgres.search import SearchVector

            qs = qs.annotate(
                markdown_search_vector=SearchVector("markdown"),
            )
        return qs


class Tag(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid_extensions.uuid7)
    name = models.CharField(max_length=128, unique=True)

    def __str__(self) -> str:
        return f"Tag: {self.name}"
