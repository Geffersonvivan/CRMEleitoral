from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.campaigns.views_frontend import kanban_view, itinerary_list, itinerary_detail, content_list

urlpatterns = [
    # Admin (apenas para alimentar dados)
    path('admin/', admin.site.urls),

    # Auth
    path('accounts/', include('apps.accounts.urls')),

    # API REST
    path('api/v1/geo/', include('apps.geography.urls')),
    path('api/v1/contacts/', include('apps.contacts.urls')),
    path('api/v1/elections/', include('apps.elections.urls')),
    path('api/v1/campaigns/', include('apps.campaigns.urls')),
    path('api/v1/events/', include('apps.events.urls')),
    path('api/v1/communications/', include('apps.communications.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
    path('api/v1/maps/', include('apps.maps.urls')),
    path('api/v1/fundraising/', include('apps.fundraising.urls')),

    # Frontend - paginas proprias
    path('contatos/', include('apps.contacts.urls_frontend')),
    path('campanhas/', include('apps.campaigns.urls_frontend')),
    path('demandas/', kanban_view),
    path('roteiros/', itinerary_list),
    path('roteiros/<int:pk>/', itinerary_detail),
    path('conteudos/', content_list),
    path('eventos/', include('apps.events.urls_frontend')),
    path('eleicoes/', include('apps.elections.urls_frontend')),

    # Home (dashboard + mapa)
    path('', include('apps.dashboard.urls_frontend')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
