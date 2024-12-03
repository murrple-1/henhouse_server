import uuid

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.db.models import Max, Q, QuerySet, Value
from django.db.models.functions import Coalesce
from django.http import Http404, HttpRequest
from django.utils import timezone
from ninja import Query
from ninja.pagination import RouterPaginated

from app_admin.security import auth_optional, must_auth
from art.models import Chapter, Story, Tag
from art.schemas import (
    ChapterInSchema,
    ChapterOutDetailsSchema,
    ChapterOutSchema,
    ChapterPatchInSchema,
    ListSchema,
    StoryInSchema,
    StoryOutDetailsSchema,
    StoryOutSchema,
    StoryPatchInSchema,
    TagOutSchema,
)

router = RouterPaginated()


@router.get("/story", response=list[StoryOutSchema], auth=auth_optional, tags=["story"])
def list_stories(request: HttpRequest, list_params: Query[ListSchema]):
    user = request.user
    filter_args: list[Q]
    if user.is_authenticated:
        filter_args = [(Q(creator=user) | Q(published_at__isnull=False))]
    else:
        filter_args = [Q(published_at__isnull=False)]

    filter_args += list_params.get_filter_args("story", request)

    return (
        Story.annotate_from_chapters(Story.objects.all())
        .filter(*filter_args)
        .order_by(*list_params.get_order_by_args("story"))
    )


@router.get(
    "/story/{story_id}",
    response=StoryOutDetailsSchema,
    auth=auth_optional,
    tags=["story"],
)
def story_details(request: HttpRequest, story_id: uuid.UUID):
    user = request.user
    filter_args: list[Q]
    if user.is_authenticated:
        filter_args = [(Q(creator=user) | Q(published_at__isnull=False))]
    else:
        filter_args = [Q(published_at__isnull=False)]

    try:
        return (
            Story.annotate_from_chapters(Story.objects.all())
            .filter(*filter_args)
            .get(uuid=story_id)
        )
    except Story.DoesNotExist:
        raise Http404


@router.post("/story", response=StoryOutSchema, auth=must_auth, tags=["story"])
def create_story(request: HttpRequest, input_story: StoryInSchema):
    user = request.user
    assert isinstance(user, AbstractBaseUser)

    tag_uuids = frozenset(input_story.tags)
    tags = list(Tag.objects.filter(uuid__in=tag_uuids))
    if len(tag_uuids) != len(tags):
        raise Http404

    with transaction.atomic():
        story = Story.objects.create(creator=user, title=input_story.title)
        story.tags.set(tags)

        return story


@router.patch(
    "/story/{story_id}", response=StoryOutSchema, auth=must_auth, tags=["story"]
)
def patch_story(
    request: HttpRequest, story_id: uuid.UUID, input_story: StoryPatchInSchema
):
    user = request.user
    assert isinstance(user, AbstractBaseUser)
    with transaction.atomic():
        try:
            story = Story.objects.get(creator=user, uuid=story_id)
        except Story.DoesNotExist:
            raise Http404

        update_fields: set[str] = set()

        if input_story.tags is not None:
            tag_uuids = frozenset(input_story.tags)
            tags = list(Tag.objects.filter(uuid__in=tag_uuids))
            if len(tag_uuids) != len(tags):
                raise Http404
            story.tags.set(tags)

        if input_story.title is not None:
            story.title = input_story.title
            update_fields.add("title")

        story.save(update_fields=update_fields)

        return story


@router.delete(
    "/story/{story_id}", response={204: None}, auth=must_auth, tags=["story"]
)
def delete_story(request: HttpRequest, story_id: uuid.UUID):
    user = request.user
    assert isinstance(user, AbstractBaseUser)
    count, _ = Story.objects.filter(creator=user, uuid=story_id).delete()
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
    user = request.user
    filter_args: list[Q]
    if user.is_authenticated:
        filter_args = [(Q(creator=user) | Q(published_at__isnull=False))]
    else:
        filter_args = [Q(published_at__isnull=False)]

    story: Story
    try:
        story = (
            Story.annotate_from_chapters(Story.objects.all())
            .filter(*filter_args)
            .get(uuid=story_id)
        )
    except Story.DoesNotExist:
        raise Http404

    if user.is_authenticated and story.creator_id == user.pk:
        return story.chapters.all()
    else:
        return story.chapters.filter(published_at__isnull=False)


@router.get(
    "/chapter/{chapter_id}",
    response=ChapterOutDetailsSchema,
    auth=auth_optional,
    tags=["chapter"],
)
def chapter_details(request: HttpRequest, chapter_id: uuid.UUID):
    user = request.user

    accessible_chapters: QuerySet[Chapter]
    if user.is_authenticated:
        accessible_chapters = Chapter.objects.filter(
            Q(story__creator=user) | Q(published_at__isnull=False)
        )
    else:
        accessible_chapters = Chapter.objects.filter(published_at__isnull=False)

    try:
        return accessible_chapters.get(uuid=chapter_id)
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
    user = request.user
    assert isinstance(user, AbstractBaseUser)
    with transaction.atomic():
        try:
            story = Story.objects.get(creator=user, uuid=story_id)
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
    user = request.user
    assert isinstance(user, AbstractBaseUser)
    with transaction.atomic():
        try:
            chapter = Chapter.objects.get(story__creator=user, uuid=chapter_id)
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
    user = request.user
    assert isinstance(user, AbstractBaseUser)
    count, _ = Chapter.objects.filter(story__creator=user, uuid=chapter_id).delete()
    if not count:
        raise Http404

    return None


@router.get("/tag", response=list[TagOutSchema], auth=auth_optional, tags=["tag"])
def list_tags(request: HttpRequest):
    return Tag.objects.all()
