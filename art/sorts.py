from query_utils.sort import DefaultDescriptor, SortConfig, standard_sort

sort_configs: dict[str, dict[str, SortConfig]] = {
    "story": {
        "uuid": SortConfig([standard_sort("uuid")], DefaultDescriptor(0, "ASC")),
        "title": SortConfig([standard_sort("title")], None),
        "synopsis": SortConfig([standard_sort("synopsis")], None),
        "author": SortConfig([standard_sort("author__username")], None),
    },
    "chapter": {
        "uuid": SortConfig([standard_sort("uuid")], DefaultDescriptor(0, "ASC")),
        "name": SortConfig([standard_sort("name")], None),
        "synopsis": SortConfig([standard_sort("synopsis")], None),
        "createdAt": SortConfig([standard_sort("created_at")], None),
        "publishedAt": SortConfig([standard_sort("published_at")], None),
    },
    "category": {
        "sortKey": SortConfig([standard_sort("sort_key")], DefaultDescriptor(0, "ASC")),
        "name": SortConfig([standard_sort("name")], None),
        "prettyName": SortConfig([standard_sort("pretty_name")], None),
    },
    "tag": {
        "name": SortConfig([standard_sort("name")], DefaultDescriptor(0, "ASC")),
        "prettyName": SortConfig([standard_sort("pretty_name")], None),
    },
}
