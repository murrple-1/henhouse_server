from django.contrib import admin
from adminsortable2.admin import SortableAdminMixin

from art.models import Chapter, ChapterReport, Story, StoryReport, Tag, Category


class ChaptersInline(admin.TabularInline):
    model = Chapter
    extra = 0


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "is_nsfw"]
    list_filter = ["is_nsfw"]
    ordering = ["title"]
    search_fields = ["title", "author__email"]
    inlines = [ChaptersInline]


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["sort_key", "pretty_name", "name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "pretty_name"]
    search_fields = ["name", "pretty_name"]


@admin.register(StoryReport)
class StoryReportAdmin(admin.ModelAdmin):
    list_display = ["story__title", "kind"]


@admin.register(ChapterReport)
class ChapterReportAdmin(admin.ModelAdmin):
    list_display = ["chapter__name", "kind"]
