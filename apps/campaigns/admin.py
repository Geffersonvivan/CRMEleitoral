from django.contrib import admin
from .models import Campaign, Task, Itinerary, ItineraryStop, Content


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ('title', 'task_type', 'phase', 'priority', 'assigned_to', 'city', 'due_date')


class ContentInline(admin.TabularInline):
    model = Content
    extra = 0
    fields = ('title', 'content_type', 'phase', 'status', 'responsible', 'due_date')


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'responsible', 'goal_contacts', 'achieved_contacts')
    list_filter = ('status', 'start_date')
    search_fields = ('name',)
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_type', 'phase', 'priority', 'assigned_to', 'city', 'region', 'due_date')
    list_filter = ('phase', 'task_type', 'priority', 'region', 'campaign')
    search_fields = ('title', 'city__name')
    autocomplete_fields = ('city', 'region', 'assigned_to', 'campaign')
    inlines = [ContentInline]


class ItineraryStopInline(admin.TabularInline):
    model = ItineraryStop
    extra = 1
    fields = ('date', 'order', 'city', 'task', 'scheduled_time', 'travel_minutes', 'is_overnight', 'notes')
    autocomplete_fields = ('city', 'task')


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'responsible', 'origin_city')
    list_filter = ('status', 'start_date')
    search_fields = ('name',)
    autocomplete_fields = ('origin_city', 'responsible')
    inlines = [ItineraryStopInline]


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'phase', 'status', 'task', 'responsible', 'due_date')
    list_filter = ('status', 'content_type', 'phase')
    search_fields = ('title', 'task__title')
    autocomplete_fields = ('task', 'responsible')
