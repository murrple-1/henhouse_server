from typing import Optional, Self

from django.db.models import OrderBy, Q
from django.http import HttpRequest
from ninja import ModelSchema, Schema
from pydantic import ConfigDict, model_validator

from art.models import Chapter, Story, Tag
from art.searches import search_fns
from art.sorts import sort_configs
from query_utils import search as searchutils
from query_utils import sort as sortutils


class StoryInSchema(ModelSchema):
    class Meta:
        model = Story
        fields = ["title", "tags"]

    @model_validator(mode="after")
    def check_title(self) -> Self:
        title = self.title
        title = title.strip()
        if len(title) < 1:
            raise ValueError("title must be non-empty")
        self.title = title
        return self


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
        fields = ["uuid", "title", "creator", "created_at", "tags"]


class ChapterInSchema(ModelSchema):
    class Meta:
        model = Chapter
        fields = ["name", "markdown"]

    @model_validator(mode="after")
    def check_name(self) -> Self:
        name = self.name
        name = name.strip()
        if len(name) < 1:
            raise ValueError("name must be non-empty")
        self.name = name
        return self

    @model_validator(mode="after")
    def check_markdown(self) -> Self:
        markdown = self.markdown
        markdown = markdown.strip()
        if len(markdown) < 1:
            raise ValueError("markdown must be non-empty")
        self.markdown = markdown
        return self


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
        fields = [
            "uuid",
            "index",
            "name",
            "markdown",
            "story",
            "created_at",
            "published_at",
        ]


class TagOutSchema(ModelSchema):
    class Meta:
        model = Tag
        fields = ["uuid", "name"]


class ListSchema(Schema):
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_default=True)

    search: str | None = None
    sort: str | None = None
    default_sort_enabled: bool = True

    def get_filter_args(self, object_name: str, request: HttpRequest) -> list[Q]:
        if self.search is None:
            return []
        else:
            return searchutils.to_filter_args(
                object_name, request, self.search, search_fns
            )

    def get_order_by_args(self, object_name: str) -> list[OrderBy]:
        sort_list = sortutils.to_sort_list(
            object_name, self.sort, self.default_sort_enabled, sort_configs
        )
        return sortutils.sort_list_to_order_by_args(
            object_name, sort_list, sort_configs
        )
