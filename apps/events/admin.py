from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'date', 'city', 'expected_attendees', 'actual_attendees', 'organizer')
    list_filter = ('event_type', 'date', 'region')
    search_fields = ('title', 'city__name')
    filter_horizontal = ('contacts_invited', 'contacts_attended')
