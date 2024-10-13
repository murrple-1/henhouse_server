from django.contrib import admin

from art.models import Chapter, Story, Tag


class ChaptersInline(admin.TabularInline):
    model = Chapter
    extra = 0


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ["title", "creator"]
    search_fields = ["title", "creator__email"]
    inlines = [ChaptersInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
