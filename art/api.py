import uuid

from django.db import transaction
from django.db.models import Max, Value
from django.db.models.functions import Coalesce
from django.http import Http404, HttpRequest
from django.utils import timezone
from ninja.pagination import RouterPaginated

from app_admin.security import auth_optional, must_auth
from art.models import Chapter, Story, Tag
from art.schemas import (
    ChapterInSchema,
    ChapterOutDetailsSchema,
    ChapterOutSchema,
    ChapterPatchInSchema,
    StoryInSchema,
    StoryOutDetailsSchema,
    StoryOutSchema,
    StoryPatchInSchema,
    TagOutSchema,
)

router = RouterPaginated()


@router.get("/story", response=list[StoryOutSchema], auth=auth_optional, tags=["story"])
def list_stories(request: HttpRequest):
    return Story.objects.all()


@router.get(
    "/story/{story_id}",
    response=StoryOutDetailsSchema,
    auth=auth_optional,
    tags=["story"],
)
def story_details(request: HttpRequest, story_id: uuid.UUID):
    try:
        return Story.objects.get(uuid=story_id)
    except Story.DoesNotExist:
        raise Http404


@router.post("/story", response=StoryOutSchema, auth=must_auth, tags=["story"])
def create_story(request: HttpRequest, input_story: StoryInSchema):
    with transaction.atomic():
        story = Story.objects.create(creator=request.user, title=input_story.title)
        story.tags.set(Tag.objects.filter(uuid__in=frozenset(input_story.tags)))

        return story


@router.patch(
    "/story/{story_id}", response=StoryOutSchema, auth=must_auth, tags=["story"]
)
def patch_story(
    request: HttpRequest, story_id: uuid.UUID, input_story: StoryPatchInSchema
):
    with transaction.atomic():
        try:
            story = Story.objects.get(creator=request.user, uuid=story_id)
        except Story.DoesNotExist:
            raise Http404

        update_fields: set[str] = set()

        if input_story.title is not None:
            story.title = input_story.title
            update_fields.add("title")

        if input_story.published is not None:
            if input_story.published:
                if story.published_at is None:
                    story.published_at = timezone.now()
            else:
                story.published_at = None

            update_fields.add("published_at")

        story.save(update_fields=update_fields)

        if input_story.tags is not None:
            story.tags.set(Tag.objects.filter(uuid__in=frozenset(input_story.tags)))

        return story


@router.delete(
    "/story/{story_id}", response={204: None}, auth=must_auth, tags=["story"]
)
def delete_story(request: HttpRequest, story_id: uuid.UUID):
    count, _ = Story.objects.filter(creator=request.user, uuid=story_id).delete()
    if not count:
        raise Http404

    return None


@router.get(
    "/story/{story_id}/chapter",
    response=list[ChapterOutSchema],
    auth=auth_optional,
    tags=["chapter"],
)
def list_chapters(request: HttpRequest, story_id: uuid.UUID):
    return Chapter.objects.filter(story__uuid=story_id)


@router.get(
    "/chapter/{chapter_id}",
    response=ChapterOutDetailsSchema,
    auth=auth_optional,
    tags=["chapter"],
)
def chapter_details(request: HttpRequest, chapter_id: uuid.UUID):
    try:
        return Chapter.objects.get(uuid=chapter_id)
    except Chapter.DoesNotExist:
        raise Http404


@router.post(
    "/story/{story_id}/chapter",
    response=ChapterOutSchema,
    auth=must_auth,
    tags=["chapter"],
)
def create_chapter(
    request: HttpRequest, story_id: uuid.UUID, input_chapter: ChapterInSchema
):
    with transaction.atomic():
        try:
            story = Story.objects.get(creator=request.user, uuid=story_id)
        except Story.DoesNotExist:
            raise Http404

        index = Chapter.objects.filter(story=story).aggregate(
            max_index=Coalesce(Max("index"), Value(0))
        )["max_index"]

        chapter = Chapter.objects.create(
            story=story,
            name=input_chapter.name,
            markdown=input_chapter.markdown,
            index=(index + 1),
        )

        return chapter


@router.patch(
    "/chapter/{chapter_id}", response=ChapterOutSchema, auth=must_auth, tags=["chapter"]
)
def patch_chapter(
    request: HttpRequest, chapter_id: uuid.UUID, input_chapter: ChapterPatchInSchema
):
    with transaction.atomic():
        try:
            chapter = Chapter.objects.get(story__creator=request.user, uuid=chapter_id)
        except Chapter.DoesNotExist:
            raise Http404

        update_fields: set[str] = set()

        if input_chapter.name is not None:
            chapter.name = input_chapter.name
            update_fields.add("name")

        if input_chapter.markdown is not None:
            chapter.markdown = input_chapter.markdown

            update_fields.add("markdown")

        chapter.save(update_fields=update_fields)

        return chapter


@router.delete(
    "/chapter/{chapter_id}", response={204: None}, auth=must_auth, tags=["chapter"]
)
def delete_chapter(request: HttpRequest, chapter_id: uuid.UUID):
    count, _ = Chapter.objects.filter(
        story__creator=request.user, uuid=chapter_id
    ).delete()
    if not count:
        raise Http404

    return None


@router.get("/tag", response=list[TagOutSchema], auth=auth_optional, tags=["tag"])
def list_tags(request: HttpRequest):
    return Tag.objects.all()
