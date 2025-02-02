import json
import sys
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from app_admin.models import User
from art.models import Category, Chapter, Story, Tag


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("default_author_username")
        parser.add_argument("default_category")

    def handle(self, *args: Any, **options: Any) -> None:
        now = timezone.now()

        default_author: User
        try:
            default_author = User.objects.get(
                username=options["default_author_username"]
            )
        except User.DoesNotExist as e:
            raise CommandError("default author not found") from e

        authors: dict[str, User] = {
            default_author.username: default_author,
        }

        default_category: Category
        try:
            default_category = Category.objects.get(name=options["default_category"])
        except Category.DoesNotExist as e:
            raise CommandError("default category not found") from e

        categories: dict[str, Category] = {
            default_category.name: default_category,
        }

        stories_json: list[dict[str, Any]] = json.load(sys.stdin)

        tag_pretty_names: set[str] = set()

        stories: list[Story] = []
        chapters: list[Chapter] = []
        for story_json in stories_json:
            story_tag_pretty_names = frozenset(story_json["tags"])
            tag_pretty_names.update(story_tag_pretty_names)

            author: User | None
            if (author_username := story_json.get("author")) is not None:
                author = authors.get(author_username)
                if author is None:
                    try:
                        author = User.objects.get(username=author_username)
                    except User.DoesNotExist:
                        author = default_author

                    authors[author_username] = author
            else:
                author = default_author

            category: Category | None
            if (category_name := story_json.get("category")) is not None:
                category = categories.get(category_name)
                if category is None:
                    try:
                        category = Category.objects.get(name=category_name)
                    except Category.DoesNotExist:
                        category = default_category

                    categories[category_name] = category
            else:
                category = default_category

            synopsis = story_json["synopsis"].strip()
            if len(synopsis) > 256:
                new_synopsis = f"{synopsis[:255]}…"
                self.stderr.write(
                    self.style.WARNING(f"'{synopsis}' rewritten to '{new_synopsis}'")
                )
                synopsis = new_synopsis

            story = Story(
                title=story_json["title"],
                synopsis=synopsis,
                author=author,
                category=category,
            )
            setattr(
                story,
                "_tag_names",
                frozenset(_tag_pretty_name_to_name(t) for t in story_tag_pretty_names),
            )
            stories.append(story)

            for i, chapter_json in enumerate(story_json["chapters"]):
                synopsis = (
                    synopsis_
                    if (synopsis_ := chapter_json["synopsis"]) != story.synopsis
                    else ""
                ).strip()
                if len(synopsis) > 256:
                    new_synopsis = f"{synopsis[:255]}…"
                    self.stderr.write(
                        self.style.WARNING(
                            f"'{synopsis}' rewritten to '{new_synopsis}'"
                        )
                    )
                    synopsis = new_synopsis

                chapters.append(
                    Chapter(
                        story=story,
                        name=chapter_json["name"],
                        synopsis=synopsis,
                        index=i,
                        markdown=chapter_json["markdown"],
                        published_at=now,
                    )
                )

        Tag.objects.bulk_create(
            (
                Tag(
                    name=_tag_pretty_name_to_name(tag_pretty_name),
                    pretty_name=tag_pretty_name,
                )
                for tag_pretty_name in tag_pretty_names
            ),
            ignore_conflicts=True,
        )
        tags_by_name: dict[str, Tag] = {
            t.name: t
            for t in Tag.objects.filter(
                name__in=frozenset(
                    _tag_pretty_name_to_name(t) for t in tag_pretty_names
                )
            )
        }

        Story.objects.bulk_create(stories, batch_size=1024)
        Chapter.objects.bulk_create(chapters, batch_size=1024)

        for story in stories:
            story.tags.set(
                tags_by_name[tag_name] for tag_name in getattr(story, "_tag_names")
            )


def _tag_pretty_name_to_name(pretty_name: str) -> str:
    return pretty_name.lower().replace(" ", "_").replace("/", "-")
