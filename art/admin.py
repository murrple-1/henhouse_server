from django.contrib import admin

from art.models import Chapter, ChapterReport, Story, StoryReport, Tag


class ChaptersInline(admin.TabularInline):
    model = Chapter
    extra = 0


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ["title", "creator", "is_nsfw"]
    list_filter = ["is_nsfw"]
    ordering = ["title"]
    search_fields = ["title", "creator__email"]
    inlines = [ChaptersInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["pretty_name", "name"]
    search_fields = ["pretty_name", "name"]


@admin.register(StoryReport)
class StoryReportAdmin(admin.ModelAdmin):
    list_display = ["story__title", "kind"]


@admin.register(ChapterReport)
class ChapterReportAdmin(admin.ModelAdmin):
    list_display = ["chapter__name", "kind"]
