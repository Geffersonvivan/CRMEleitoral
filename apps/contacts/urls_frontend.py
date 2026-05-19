from django.urls import path
from .views_frontend import contact_list, contact_detail, company_list

app_name = 'contacts_frontend'

urlpatterns = [
    path('', contact_list, name='list'),
    path('<int:pk>/', contact_detail, name='detail'),
    path('empresas/', company_list, name='companies'),
]
