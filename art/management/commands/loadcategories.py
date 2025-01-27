import json
import sys
from typing import Any

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.db.models.functions import Coalesce

from art.models import Category


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:
        categories_json: list[dict[str, Any]] = json.load(sys.stdin)

        sort_key: int = (
            Category.objects.aggregate(max_sort_key=Coalesce(Max("sort_key"), -1))[
                "max_sort_key"
            ]
            + 1
        )

        categories: list[Category] = []

        for category_json in categories_json:
            name = category_json["name"]
            pretty_name = category_json["pretty_name"]

            description = category_json.get("description", "")

            categories.append(
                Category(
                    name=name,
                    pretty_name=pretty_name,
                    description=description,
                    sort_key=sort_key,
                )
            )

            sort_key += 1

        Category.objects.bulk_create(
            categories,
            batch_size=1024,
            update_conflicts=True,
            unique_fields=("name",),
            update_fields=("pretty_name", "description"),
        )
