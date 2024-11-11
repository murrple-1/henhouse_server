import json
import sys
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from app_admin.models import User
from art.models import Chapter, Story, Tag


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("default_creator_username")

    def handle(self, *args: Any, **options: Any) -> None:
        now = timezone.now()
        default_creator: User
        try:
            default_creator = User.objects.get(
                username=options["default_creator_username"]
            )
        except User.DoesNotExist as e:
            raise CommandError("default creator not found") from e

        creators: dict[str, User] = {
            default_creator.username: default_creator,
        }

        stories_json: list[dict[str, Any]] = json.load(sys.stdin)

        tag_names: set[str] = set()

        stories: list[Story] = []
        chapters: list[Chapter] = []
        for story_json in stories_json:
            story_tag_names = frozenset(story_json["tags"])
            tag_names.update(story_tag_names)

            creator: User | None
            if (creator_username := story_json.get("creator")) is not None:
                creator = creators.get(creator_username)
                if creator is None:
                    try:
                        creator = User.objects.get(username=creator_username)
                    except User.DoesNotExist:
                        creator = default_creator

                    creators[creator_username] = creator
            else:
                creator = default_creator

            story = Story(title=story_json["title"], creator=creator)
            setattr(story, "_tag_names", story_tag_names)
            stories.append(story)

            for i, chapter_json in enumerate(story_json["chapters"]):
                chapters.append(
                    Chapter(
                        story=story,
                        name=chapter_json["name"],
                        index=i,
                        markdown=chapter_json["markdown"],
                        published_at=now,
                    )
                )

        tags = Tag.objects.bulk_create(
            (Tag(name=tag_name) for tag_name in tag_names), ignore_conflicts=True
        )
        tags_by_name: dict[str, Tag] = {t.name: t for t in tags}

        Story.objects.bulk_create(stories, batch_size=1024)
        Chapter.objects.bulk_create(chapters, batch_size=1024)

        for story in stories:
            story.tags.set(
                tags_by_name[tag_name] for tag_name in getattr(story, "_tag_names")
            )
