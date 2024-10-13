import uuid

from django.http import Http404, HttpRequest
from ninja import Router

from art.models import Chapter, Story, Tag
from art.schemas import (
    ChapterOutDetailsSchema,
    ChapterOutSchema,
    StoryOutDetailsSchema,
    StoryOutSchema,
    TagOutSchema,
)

router = Router()


@router.get("/story", response=list[StoryOutSchema])
def list_stories(request: HttpRequest):
    return Story.objects.all()


@router.get("/story/{story_id}", response=StoryOutDetailsSchema)
def story_details(request: HttpRequest, story_id: uuid.UUID):
    try:
        return Story.objects.get(uuid=story_id)
    except Story.DoesNotExist:
        raise Http404


@router.get("/story/{story_id}/chapter", response=list[ChapterOutSchema])
def list_chapters(request: HttpRequest, story_id: uuid.UUID):
    return Chapter.objects.filter(story__uuid=story_id)


@router.get("/chapter/{chapter_id}", response=ChapterOutDetailsSchema)
def chapter_details(request: HttpRequest, chapter_id: uuid.UUID):
    try:
        return Chapter.objects.get(uuid=chapter_id)
    except Chapter.DoesNotExist:
        raise Http404
