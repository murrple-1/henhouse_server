from typing import Optional

from django.db.models import OrderBy, Q
from django.http import HttpRequest
from ninja import ModelSchema, Schema
from pydantic import ConfigDict

from art.models import Chapter, Story, Tag
from art.searches import search_fns
from art.sorts import sort_configs
from query_utils import search as searchutils
from query_utils import sort as sortutils


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
        fields = ["uuid", "title", "creator", "created_at", "tags"]


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
