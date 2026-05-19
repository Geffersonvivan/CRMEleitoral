from django.urls import path
from .views_frontend import elections_dashboard

app_name = 'elections_frontend'

urlpatterns = [
    path('', elections_dashboard, name='dashboard'),
]
