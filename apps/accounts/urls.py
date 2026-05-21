from django.urls import path
from django.contrib.auth import views as auth_views
from .views import user_list, login_redirect
from .views_usuarios import usuarios_api, usuario_detalhe_api, regioes_api

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('redirect/', login_redirect, name='login-redirect'),
    path('api/users/', user_list, name='user-list'),

    # API de gestão de usuários
    path('api/v1/accounts/users/', usuarios_api, name='usuarios-api'),
    path('api/v1/accounts/users/<int:pk>/', usuario_detalhe_api, name='usuario-detalhe-api'),
    path('api/v1/accounts/regioes/', regioes_api, name='regioes-api'),
]
