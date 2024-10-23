import uuid

from django.db import transaction
from django.http import Http404, HttpRequest
from ninja.pagination import RouterPaginated

from app_admin.security import auth_optional, must_auth
from art.models import Chapter, Story, Tag
from art.schemas import (
    ChapterOutDetailsSchema,
    ChapterOutSchema,
    StoryInSchema,
    StoryOutDetailsSchema,
    StoryOutSchema,
    TagOutSchema,
)

router = RouterPaginated()


@router.get("/story", response=list[StoryOutSchema], auth=auth_optional)
def list_stories(request: HttpRequest):
    return Story.objects.all()


@router.get("/story/{story_id}", response=StoryOutDetailsSchema, auth=auth_optional)
def story_details(request: HttpRequest, story_id: uuid.UUID):
    try:
        return Story.objects.get(uuid=story_id)
    except Story.DoesNotExist:
        raise Http404


@router.post("/story", response=StoryOutSchema, auth=must_auth)
def create_story(request: HttpRequest, input_story: StoryInSchema):
    with transaction.atomic():
        story = Story.objects.create(creator=request.user, title=input_story.title)
        story.tags.set(Tag.objects.filter(name__in=frozenset(input_story.tags)))

        return story


@router.get(
    "/story/{story_id}/chapter", response=list[ChapterOutSchema], auth=auth_optional
)
def list_chapters(request: HttpRequest, story_id: uuid.UUID):
    return Chapter.objects.filter(story__uuid=story_id)


@router.get(
    "/chapter/{chapter_id}", response=ChapterOutDetailsSchema, auth=auth_optional
)
def chapter_details(request: HttpRequest, chapter_id: uuid.UUID):
    try:
        return Chapter.objects.get(uuid=chapter_id)
    except Chapter.DoesNotExist:
        raise Http404


@router.get("/tag", response=list[TagOutSchema], auth=auth_optional)
def list_tags(request: HttpRequest):
    return Tag.objects.all()
