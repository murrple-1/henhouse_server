from query_utils.sort import DefaultDescriptor, SortConfig, standard_sort

sort_configs: dict[str, dict[str, SortConfig]] = {
    "story": {
        "uuid": SortConfig([standard_sort("uuid")], DefaultDescriptor(0, "ASC")),
        "title": SortConfig([standard_sort("title")], None),
    },
    "chapter": {
        "uuid": SortConfig([standard_sort("uuid")], DefaultDescriptor(0, "ASC")),
        "name": SortConfig([standard_sort("name")], None),
    },
    "tag": {
        "uuid": SortConfig([standard_sort("uuid")], None),
        "name": SortConfig([standard_sort("uuid")], DefaultDescriptor(0, "ASC")),
        "prettyName": SortConfig([standard_sort("pretty_name")], None),
    },
}
