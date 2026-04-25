from django.contrib import admin

from knowledgebase.models import ReadHistory, Tutorial, TutorialImage, TutorialVideo


class TutorialImageInline(admin.TabularInline):
    model = TutorialImage
    extra = 1


class TutorialVideoInline(admin.TabularInline):
    model = TutorialVideo
    extra = 1


@admin.register(Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "created_by", "is_published", "updated_at")
    list_filter = ("department", "is_published")
    search_fields = ("title", "description", "content")
    inlines = [TutorialImageInline, TutorialVideoInline]


@admin.register(ReadHistory)
class ReadHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "tutorial", "read_at")
    list_filter = ("user", "tutorial__department")

# Register your models here.
