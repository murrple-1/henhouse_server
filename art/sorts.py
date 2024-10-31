from query_utils.sort import DefaultDescriptor, SortConfig, standard_sort

sort_configs: dict[str, dict[str, SortConfig]] = {
    "story": {
        "uuid": SortConfig([standard_sort("uuid")], DefaultDescriptor(0, "ASC")),
        "text": SortConfig([standard_sort("text")], None),
    },
}