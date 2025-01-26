# TODO replace with regular `uuid` module when finalized in Python
import uuid_extensions
from django.conf import settings
from django.db import connection, models
from django.utils import timezone


class Story(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid_extensions.uuid7)
    title = models.TextField()
    synopsis = models.CharField(max_length=256)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="stories", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(default=timezone.now)
    is_nsfw = models.BooleanField(default=False)
    category = models.ForeignKey(
        "Category", related_name="stories", null=True, on_delete=models.PROTECT
    )
    tags = models.ManyToManyField("Tag", related_name="stories", blank=True)
    favorites_of = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="favorite_stories", blank=True
    )

    @staticmethod
    def annotate_from_chapters(
        qs: models.QuerySet["Story"],
    ) -> models.QuerySet["Story"]:
        chapters = Chapter.objects.filter(story_id=models.OuterRef("uuid"))
        return qs.annotate(
            published_at=chapters.values("story_id")
            .annotate(min_published_at=models.Min("published_at"))
            .values("min_published_at")
        )

    @staticmethod
    def annotate_search_vectors(
        qs: models.QuerySet["Story"],
    ) -> models.QuerySet["Story"]:
        if connection.vendor == "postgresql":  # pragma: no cover
            from django.contrib.postgres.search import SearchVectorField
            from django.db.models.expressions import RawSQL

            qs = qs.annotate(
                title_search_vector=RawSQL(
                    "title_search_vector", [], output_field=SearchVectorField()
                ),
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
    synopsis = models.CharField(max_length=256)
    index = models.PositiveIntegerField()
    markdown = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    published_at = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def annotate_search_vectors(
        qs: models.QuerySet["Chapter"],
    ) -> models.QuerySet["Chapter"]:
        if connection.vendor == "postgresql":  # pragma: no cover
            from django.contrib.postgres.search import SearchVectorField
            from django.db.models.expressions import RawSQL

            qs = qs.annotate(
                markdown_search_vector=RawSQL(
                    "markdown_search_vector", [], output_field=SearchVectorField()
                ),
            )
        return qs


class Category(models.Model):
    class Meta:
        indexes = (models.Index(fields=("sort_key",)),)

    name = models.CharField(primary_key=True, max_length=128, blank=False)
    pretty_name = models.CharField(max_length=128, blank=False)
    description = models.TextField(default="", blank=True)
    sort_key = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"Category: {self.pretty_name} ({self.name})"


class Tag(models.Model):
    name = models.CharField(primary_key=True, max_length=128, blank=False)
    pretty_name = models.CharField(max_length=128, blank=False)

    def __str__(self) -> str:
        return f"Tag: {self.pretty_name} ({self.name})"


class ReportKind(models.IntegerChoices):
    OTHER = 0
    DMCA = 1
    ABUSE = 2


class StoryReport(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid_extensions.uuid7)
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    kind = models.IntegerField(choices=ReportKind.choices)
    details = models.CharField(max_length=1024)
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class ChapterReport(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid_extensions.uuid7)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    kind = models.IntegerField(choices=ReportKind.choices)
    details = models.CharField(max_length=1024)
    submitter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
