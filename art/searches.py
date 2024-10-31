from typing import Callable

from django.db import connection
from django.db.models import Q
from django.http import HttpRequest

from query_utils.search.convertto import UuidList

search_fns: dict[str, dict[str, Callable[[HttpRequest, str], Q]]] = {
    "story": {
        "uuid": lambda request, search_obj: Q(uuid__in=UuidList.convertto(search_obj)),
        "title_exact": lambda request, search_obj: Q(title__iexact=search_obj),
    },
}

if connection.vendor == "postgresql":  # pragma: no cover
    search_fns["story"]["title"] = lambda request, search_obj: Q(
        title_search_vector=search_obj
    )
else:
    search_fns["feed"]["title"] = lambda request, search_obj: Q(
        title__icontains=search_obj
    )
