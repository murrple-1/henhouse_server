import datetime
from typing import Optional, Self

from django.db.models import Min, OrderBy, Q
from django.http import HttpRequest
from ninja import Field, ModelSchema, Schema
from pydantic import model_validator

from art.models import Chapter, Story, Tag
from art.searches import search_fns
from art.sorts import sort_configs
from query_utils import search as searchutils
from query_utils import sort as sortutils


class StoryInSchema(ModelSchema):
    class Meta:
        model = Story
        fields = ["title", "synopsis", "tags"]

    @model_validator(mode="after")
    def check_title(self) -> Self:
        title = self.title
        title = title.strip()
        if len(title) < 1:
            raise ValueError("title must be non-empty")
        self.title = title
        return self

    @model_validator(mode="after")
    def check_synopsis(self) -> Self:
        synopsis = self.synopsis
        synopsis = synopsis.strip()
        if len(synopsis) < 1:
            raise ValueError("synopsis must be non-empty")
        self.synopsis = synopsis
        return self


class StoryPatchInSchema(ModelSchema):
    published: Optional[bool] = None

    class Meta:
        model = Story
        fields = ["title", "synopsis", "tags"]
        fields_optional = "__all__"

    @model_validator(mode="after")
    def check_title(self) -> Self:
        title = self.title
        if title is not None:
            title = title.strip()
            if len(title) < 1:
                raise ValueError("title must be non-empty")
            self.title = title
        return self

    @model_validator(mode="after")
    def check_synopsis(self) -> Self:
        synopsis = self.synopsis
        if synopsis is not None:
            synopsis = synopsis.strip()
            if len(synopsis) < 1:
                raise ValueError("synopsis must be non-empty")
            self.synopsis = synopsis
        return self


class StoryOutSchema(ModelSchema):
    createdAt: datetime.datetime = Field(datetime.datetime.min, alias="created_at")
    publishedAt: datetime.datetime = Field(datetime.datetime.min)

    class Meta:
        model = Story
        fields = ["uuid", "title", "synopsis", "creator"]

    @staticmethod
    def resolve_publishedAt(obj: Story):
        return Chapter.objects.filter(story=obj).aggregate(
            published_at=Min("published_at")
        )["published_at"]


class StoryOutDetailsSchema(ModelSchema):
    createdAt: datetime.datetime = Field(datetime.datetime.min, alias="created_at")

    class Meta:
        model = Story
        fields = ["uuid", "title", "synopsis", "creator", "tags"]


class ChapterInSchema(ModelSchema):
    class Meta:
        model = Chapter
        fields = ["name", "synopsis", "markdown"]

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
        fields = ["name", "synopsis", "markdown"]
        fields_optional = "__all__"

    @model_validator(mode="after")
    def check_name(self) -> Self:
        name = self.name
        if name is not None:
            name = name.strip()
            if len(name) < 1:
                raise ValueError("name must be non-empty")
            self.name = name
        return self

    @model_validator(mode="after")
    def check_markdown(self) -> Self:
        markdown = self.markdown
        if markdown is not None:
            markdown = markdown.strip()
            if len(markdown) < 1:
                raise ValueError("markdown must be non-empty")
            self.markdown = markdown
        return self


class ChapterOutSchema(ModelSchema):
    class Meta:
        model = Chapter
        fields = ["uuid", "index", "name", "synopsis"]


class ChapterOutDetailsSchema(ModelSchema):
    createdAt: datetime.datetime = Field(datetime.datetime.min, alias="created_at")
    publishedAt: datetime.datetime | None = Field(None, alias="published_at")

    class Meta:
        model = Chapter
        fields = [
            "uuid",
            "index",
            "name",
            "synopsis",
            "markdown",
            "story",
        ]


class TagOutSchema(ModelSchema):
    class Meta:
        model = Tag
        fields = ["name"]


class TagOutDetailsSchema(ModelSchema):
    prettyName: str = Field("", alias="pretty_name")

    class Meta:
        model = Tag
        fields = ["name", "description"]


class ListInSchema(Schema):
    search: str | None = None
    sort: str | None = None
    default_sort_enabled: bool = Field(True, alias="defaultSortEnabled")

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
