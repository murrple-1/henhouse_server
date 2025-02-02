from typing import Callable

from django.db import connection
from django.db.models import Q, Exists, Min, OuterRef
from django.http import HttpRequest

from art.models import Chapter
from query_utils.search.convertto import (
    Bool,
    DateTime,
    DateTimeDeltaRange,
    DateTimeRange,
    UuidList,
    CustomConvertTo,
)


class StrList(CustomConvertTo):
    @staticmethod
    def convertto(search_obj: str) -> list[str]:
        return search_obj.split(",")


def _story_isPublished(request: HttpRequest, search_obj: str) -> Q:
    q = Q(
        Exists(
            Chapter.objects.filter(
                story_id=OuterRef("uuid"), published_at__isnull=False
            )
        )
    )

    if not Bool.convertto(search_obj):
        q = ~q

    return q


search_fns: dict[str, dict[str, Callable[[HttpRequest, str], Q]]] = {
    "story": {
        "uuid": lambda request, search_obj: Q(uuid__in=UuidList.convertto(search_obj)),
        "title_exact": lambda request, search_obj: Q(title__iexact=search_obj),
        "synopsis": lambda request, search_obj: Q(synopsis__icontains=search_obj),
        "author": lambda request, search_obj: Q(
            author_id__in=UuidList.convertto(search_obj)
        ),
        "category": lambda request, search_obj: Q(
            category_id__in=StrList.convertto(search_obj)
        ),
        "createdAt": lambda request, search_obj: Q(
            created_at__range=DateTimeRange.convertto(search_obj)
        ),
        "createdAt_exact": lambda request, search_obj: Q(
            created_at=DateTime.convertto(search_obj)
        ),
        "createdAt_delta": lambda request, search_obj: Q(
            created_at__range=DateTimeDeltaRange.convertto(search_obj)
        ),
        "publishedAt": lambda request, search_obj: Q(
            uuid__in=Chapter.objects.filter(story_id=OuterRef("uuid"))
            .annotate(min_published_at=Min("published_at"))
            .filter(min_published_at__range=DateTimeRange.convertto(search_obj))
            .values("story_id")
        ),
        "publishedAt_exact": lambda request, search_obj: Q(
            uuid__in=Chapter.objects.filter(story_id=OuterRef("uuid"))
            .annotate(min_published_at=Min("published_at"))
            .filter(min_published_at=DateTime.convertto(search_obj))
            .values("story_id")
        ),
        "publishedAt_delta": lambda request, search_obj: Q(
            uuid__in=Chapter.objects.filter(story_id=OuterRef("uuid"))
            .annotate(min_published_at=Min("published_at"))
            .filter(min_published_at__range=DateTimeDeltaRange.convertto(search_obj))
            .values("story_id")
        ),
        "isPublished": _story_isPublished,
    },
    "chapter": {
        "uuid": lambda request, search_obj: Q(uuid__in=UuidList.convertto(search_obj)),
        "story": lambda request, search_obj: Q(
            story_id__in=UuidList.convertto(search_obj)
        ),
        "name": lambda request, search_obj: Q(name__icontains=search_obj),
        "name_exact": lambda request, search_obj: Q(name__iexact=search_obj),
        "synopsis": lambda request, search_obj: Q(synopsis__icontains=search_obj),
        "createdAt": lambda request, search_obj: Q(
            created_at__range=DateTimeRange.convertto(search_obj)
        ),
        "createdAt_exact": lambda request, search_obj: Q(
            created_at=DateTime.convertto(search_obj)
        ),
        "createdAt_delta": lambda request, search_obj: Q(
            created_at__range=DateTimeDeltaRange.convertto(search_obj)
        ),
        "publishedAt": lambda request, search_obj: Q(
            published_at__range=DateTimeRange.convertto(search_obj)
        ),
        "publishedAt_exact": lambda request, search_obj: Q(
            published_at=DateTime.convertto(search_obj)
        ),
        "publishedAt_delta": lambda request, search_obj: Q(
            published_at__range=DateTimeDeltaRange.convertto(search_obj)
        ),
        "isPublished": lambda request, search_obj: Q(
            published_at__isnull=not Bool.convertto(search_obj)
        ),
    },
    "category": {
        "name": lambda request, search_obj: Q(name__icontains=search_obj),
        "name_exact": lambda request, search_obj: Q(name__iexact=search_obj),
        "prettyName": lambda request, search_obj: Q(pretty_name__icontains=search_obj),
        "prettyName_exact": lambda request, search_obj: Q(
            pretty_name__iexact=search_obj
        ),
    },
    "tag": {
        "name": lambda request, search_obj: Q(name__icontains=search_obj),
        "name_exact": lambda request, search_obj: Q(name__iexact=search_obj),
        "prettyName": lambda request, search_obj: Q(pretty_name__icontains=search_obj),
        "prettyName_exact": lambda request, search_obj: Q(
            pretty_name__iexact=search_obj
        ),
    },
}

if connection.vendor == "postgresql":  # pragma: no cover

    def _story_storyText(request: HttpRequest, search_obj: str) -> Q:
        return Q(
            uuid__in=Chapter.annotate_search_vectors(Chapter.objects.all())
            .filter(published_at__isnull=False, markdown_search_vector=search_obj)
            .values("story_id")
        )

    search_fns["story"]["title"] = lambda request, search_obj: Q(
        title_search_vector=search_obj
    )
    search_fns["story"]["storyText"] = _story_storyText
    search_fns["chapter"]["text"] = lambda request, search_obj: Q(
        markdown_search_vector=search_obj
    )
else:

    def _story_storyText(request: HttpRequest, search_obj: str) -> Q:
        return Q(
            uuid__in=Chapter.objects.filter(
                published_at__isnull=False, markdown__icontains=search_obj
            ).values("story_id")
        )

    search_fns["story"]["title"] = lambda request, search_obj: Q(
        title__icontains=search_obj
    )
    search_fns["story"]["storyText"] = _story_storyText
    search_fns["chapter"]["text"] = lambda request, search_obj: Q(
        markdown__icontains=search_obj
    )
