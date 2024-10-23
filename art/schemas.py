from ninja import ModelSchema

from art.models import Chapter, Story, Tag


class StoryInSchema(ModelSchema):
    tags: list[str]

    class Meta:
        model = Story
        fields = ["title"]


class StoryOutSchema(ModelSchema):
    class Meta:
        model = Story
        fields = ["uuid", "title"]


class StoryOutDetailsSchema(ModelSchema):
    class Meta:
        model = Story
        fields = ["uuid", "title", "creator", "created_at", "published_at", "tags"]


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
