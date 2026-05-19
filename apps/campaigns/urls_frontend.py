from django.urls import path
from .views_frontend import campaign_list, kanban_view

app_name = 'campaigns_frontend'

urlpatterns = [
    path('', campaign_list, name='list'),
    path('demandas/', kanban_view, name='kanban'),
]
