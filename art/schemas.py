from typing import Optional

from ninja import ModelSchema

from art.models import Chapter, Story, Tag


class StoryInSchema(ModelSchema):
    class Meta:
        model = Story
        fields = ["title", "tags"]


class StoryPatchInSchema(ModelSchema):
    published: Optional[bool] = None

    class Meta:
        model = Story
        fields = ["title", "tags"]
        fields_optional = "__all__"


class StoryOutSchema(ModelSchema):
    class Meta:
        model = Story
        fields = ["uuid", "title"]


class StoryOutDetailsSchema(ModelSchema):
    class Meta:
        model = Story
        fields = ["uuid", "title", "creator", "created_at", "published_at", "tags"]


class ChapterInSchema(ModelSchema):
    class Meta:
        model = Chapter
        fields = ["name", "markdown"]


class ChapterPatchInSchema(ModelSchema):
    class Meta:
        model = Chapter
        fields = ["name", "markdown"]
        fields_optional = "__all__"


class ChapterOutSchema(ModelSchema):
    class Meta:
        model = Chapter
        fields = ["uuid", "index", "name"]


class ChapterOutDetailsSchema(ModelSchema):
    class Meta:
        model = Chapter
        fields = ["uuid", "index", "name", "markdown", "story"]


class TagOutSchema(ModelSchema):
    class Meta:
        model = Tag
        fields = ["uuid", "name"]
