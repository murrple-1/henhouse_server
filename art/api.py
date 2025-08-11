import uuid
from typing import Iterable

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.db.models import Max, Q, QuerySet, Value
from django.db.models.functions import Coalesce
from django.http import Http404, HttpRequest
from ninja import Query
from ninja.pagination import RouterPaginated

from app_admin.security import auth_optional, must_auth
from art.models import Category, Chapter, Story, Tag
from art.schemas import (
    CategoryOutDetailsSchema,
    CategoryOutSchema,
    ChapterInSchema,
    ChapterOutDetailsSchema,
    ChapterOutSchema,
    ChapterPatchInSchema,
    ListInSchema,
    StoryInSchema,
    StoryOutDetailsSchema,
    StoryOutSchema,
    StoryPatchInSchema,
    TagOutDetailsSchema,
    TagOutSchema,
)

# TODO maybe improve performance https://archive.li/rxzuU ?
router = RouterPaginated()


@router.get("/story", response=list[StoryOutSchema], auth=auth_optional, tags=["story"])
async def list_stories(request: HttpRequest, list_params: Query[ListInSchema]):
    user = await request.auser()
    filter_args: list[Q]
    if user.is_authenticated:
        filter_args = [(Q(author=user) | Q(published_at__isnull=False))]
    else:
        filter_args = [Q(published_at__isnull=False)]

    filter_args += list_params.get_filter_args("story", request)

    return (
        StoryOutSchema.annotate_for_schema(
            Story.annotate_search_vectors(
                Story.annotate_from_chapters(Story.objects.all())
            )
        )
        .filter(*filter_args)
        .order_by(*list_params.get_order_by_args("story"))
    )


@router.get(
    "/story/{story_id}",
    response=StoryOutDetailsSchema,
    auth=auth_optional,
    tags=["story"],
)
async def story_details(request: HttpRequest, story_id: uuid.UUID):
    user = await request.auser()
    filter_args: list[Q]
    if user.is_authenticated:
        filter_args = [(Q(author=user) | Q(published_at__isnull=False))]
    else:
        filter_args = [Q(published_at__isnull=False)]

    try:
        return await (
            StoryOutDetailsSchema.annotate_for_schema(
                Story.annotate_from_chapters(Story.objects.all())
            )
            .prefetch_related("tags")
            .filter(*filter_args)
            .aget(uuid=story_id)
        )
    except Story.DoesNotExist:
        raise Http404


@router.post("/story", response=StoryOutSchema, auth=must_auth, tags=["story"])
async def create_story(request: HttpRequest, input_story: StoryInSchema):
    user = await request.auser()
    assert isinstance(user, AbstractBaseUser)

    category: Category
    try:
        category = await Category.objects.aget(name=input_story.category)
    except Category.DoesNotExist:
        raise Http404

    tag_uuids = frozenset(input_story.tags)
    tags: list[Tag] = [t async for t in Tag.objects.filter(name__in=tag_uuids)]
    if len(tag_uuids) != len(tags):
        raise Http404

    return await _create_story_transaction(user, input_story, category, tags)


@sync_to_async
def _create_story_transaction(
    user: AbstractBaseUser,
    input_story: StoryInSchema,
    category: Category,
    tags: list[Tag],
) -> Story:
    with transaction.atomic():
        story = Story.objects.create(
            author=user,
            title=input_story.title,
            synopsis=input_story.synopsis,
            category=category,
        )
        story.tags.set(tags)
        StoryOutSchema.setattr_for_schema(story)

        return story


@router.patch(
    "/story/{story_id}", response=StoryOutSchema, auth=must_auth, tags=["story"]
)
async def patch_story(
    request: HttpRequest, story_id: uuid.UUID, input_story: StoryPatchInSchema
):
    user = await request.auser()
    assert isinstance(user, AbstractBaseUser)

    try:
        story = await StoryOutSchema.annotate_for_schema(Story.objects.all()).aget(
            author=user, uuid=story_id
        )
    except Story.DoesNotExist:
        raise Http404

    update_fields: set[str] = set()

    if input_story.title is not None:
        story.title = input_story.title
        update_fields.add("title")

    if input_story.synopsis is not None:
        story.synopsis = input_story.synopsis
        update_fields.add("synopsis")

    if input_story.category is not None:
        category: Category
        try:
            category = await Category.objects.aget(name=input_story.category)
        except Category.DoesNotExist:
            raise Http404

        story.category = category
        update_fields.add("category")

    tags: Iterable[Tag] | None = None
    if input_story.tags is not None:
        tag_uuids = frozenset(input_story.tags)
        tags = [t async for t in Tag.objects.filter(name__in=tag_uuids)]
        if len(tag_uuids) != len(tags):
            raise Http404

    await _patch_story_transaction(story, update_fields, tags)

    return story


@sync_to_async
def _patch_story_transaction(
    story: Story, update_fields: set[str], tags: Iterable[Tag] | None
) -> None:
    with transaction.atomic():
        story.save(update_fields=update_fields)

        if tags is not None:
            story.tags.set(tags)


@router.delete(
    "/story/{story_id}", response={204: None}, auth=must_auth, tags=["story"]
)
async def delete_story(request: HttpRequest, story_id: uuid.UUID):
    user = await request.auser()
    assert isinstance(user, AbstractBaseUser)
    count, _ = await Story.objects.filter(author=user, uuid=story_id).adelete()
    if not count:
        raise Http404

    return None


@router.get(
    "/story/{story_id}/chapter",
    response=list[ChapterOutSchema],
    auth=auth_optional,
    tags=["chapter"],
)
async def list_chapters(request: HttpRequest, story_id: uuid.UUID):
    user = await request.auser()
    filter_args: list[Q]
    if user.is_authenticated:
        filter_args = [(Q(author=user) | Q(published_at__isnull=False))]
    else:
        filter_args = [Q(published_at__isnull=False)]

    story: Story
    try:
        story = await (
            Story.annotate_from_chapters(Story.objects.all())
            .filter(*filter_args)
            .aget(uuid=story_id)
        )
    except Story.DoesNotExist:
        raise Http404

    chapter_qs: QuerySet[Chapter]
    if user.is_authenticated and story.author_id == user.pk:
        chapter_qs = story.chapters.all()
    else:
        chapter_qs = story.chapters.filter(published_at__isnull=False)

    return chapter_qs


@router.get(
    "/chapter/{chapter_id}",
    response=ChapterOutDetailsSchema,
    auth=auth_optional,
    tags=["chapter"],
)
async def chapter_details(request: HttpRequest, chapter_id: uuid.UUID):
    user = await request.auser()

    accessible_chapters: QuerySet[Chapter]
    if user.is_authenticated:
        accessible_chapters = Chapter.objects.filter(
            Q(story__author=user) | Q(published_at__isnull=False)
        )
    else:
        accessible_chapters = Chapter.objects.filter(published_at__isnull=False)

    try:
        return await accessible_chapters.aget(uuid=chapter_id)
    except Chapter.DoesNotExist:
        raise Http404


@router.post(
    "/story/{story_id}/chapter",
    response=ChapterOutSchema,
    auth=must_auth,
    tags=["chapter"],
)
async def create_chapter(
    request: HttpRequest, story_id: uuid.UUID, input_chapter: ChapterInSchema
):
    user = await request.auser()

    try:
        story = await Story.objects.aget(author=user, uuid=story_id)
    except Story.DoesNotExist:
        raise Http404

    index = (
        await Chapter.objects.filter(story=story).aaggregate(
            max_index=Coalesce(Max("index"), Value(-1))
        )
    )["max_index"]

    chapter = await Chapter.objects.acreate(
        story=story,
        name=input_chapter.name,
        synopsis=input_chapter.synopsis,
        markdown=input_chapter.markdown,
        index=(index + 1),
    )

    return chapter


@router.patch(
    "/chapter/{chapter_id}", response=ChapterOutSchema, auth=must_auth, tags=["chapter"]
)
async def patch_chapter(
    request: HttpRequest, chapter_id: uuid.UUID, input_chapter: ChapterPatchInSchema
):
    user = await request.auser()
    assert isinstance(user, AbstractBaseUser)

    try:
        chapter = await Chapter.objects.aget(story__author=user, uuid=chapter_id)
    except Chapter.DoesNotExist:
        raise Http404

    update_fields: set[str] = set()

    if input_chapter.name is not None:
        chapter.name = input_chapter.name
        update_fields.add("name")

    if input_chapter.synopsis is not None:
        chapter.synopsis = input_chapter.synopsis
        update_fields.add("synopsis")

    if input_chapter.markdown is not None:
        chapter.markdown = input_chapter.markdown
        update_fields.add("markdown")

    await chapter.asave(update_fields=update_fields)

    return chapter


@router.delete(
    "/chapter/{chapter_id}", response={204: None}, auth=must_auth, tags=["chapter"]
)
async def delete_chapter(request: HttpRequest, chapter_id: uuid.UUID):
    user = await request.auser()
    assert isinstance(user, AbstractBaseUser)
    count, _ = await Chapter.objects.filter(
        story__author=user, uuid=chapter_id
    ).adelete()
    if not count:
        raise Http404

    return None


@router.get(
    "/category",
    response=list[CategoryOutSchema],
    auth=auth_optional,
    tags=["category"],
)
async def list_categories(request: HttpRequest, list_params: Query[ListInSchema]):
    filter_args: list[Q] = list_params.get_filter_args("category", request)
    return Category.objects.filter(*filter_args).order_by(
        *list_params.get_order_by_args("category")
    )


@router.get(
    "/category/{category_name}",
    response=CategoryOutDetailsSchema,
    auth=auth_optional,
    tags=["category"],
)
async def category_details(request: HttpRequest, category_name: str):
    try:
        return await Category.objects.aget(name=category_name)
    except Category.DoesNotExist:
        raise Http404


@router.get("/tag", response=list[TagOutSchema], auth=auth_optional, tags=["tag"])
async def list_tags(request: HttpRequest, list_params: Query[ListInSchema]):
    filter_args: list[Q] = list_params.get_filter_args("tag", request)
    return Tag.objects.filter(*filter_args).order_by(
        *list_params.get_order_by_args("tag")
    )


@router.get(
    "/tag/{tag_name}",
    response=TagOutDetailsSchema,
    auth=auth_optional,
    tags=["tag"],
)
async def tag_details(request: HttpRequest, tag_name: str):
    try:
        return await Tag.objects.aget(name=tag_name)
    except Tag.DoesNotExist:
        raise Http404
