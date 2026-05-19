from django.urls import path
from .views_frontend import event_list

app_name = 'events_frontend'

urlpatterns = [
    path('', event_list, name='list'),
]
