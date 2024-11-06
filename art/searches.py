from typing import Callable

from django.db import connection
from django.db.models import Q
from django.http import HttpRequest

from art.models import Chapter
from query_utils.search.convertto import UuidList

search_fns: dict[str, dict[str, Callable[[HttpRequest, str], Q]]] = {
    "story": {
        "uuid": lambda request, search_obj: Q(uuid__in=UuidList.convertto(search_obj)),
        "title_exact": lambda request, search_obj: Q(title__iexact=search_obj),
    },
    "chapter": {
        "uuid": lambda request, search_obj: Q(uuid__in=UuidList.convertto(search_obj)),
        "name": lambda request, search_obj: Q(name__icontains=search_obj),
        "name_exact": lambda request, search_obj: Q(title__iexact=search_obj),
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
