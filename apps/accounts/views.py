from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import User


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list(request):
    """Lista simples de usuarios para selects."""
    users = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    data = [
        {'id': u.id, 'name': u.get_full_name() or u.username}
        for u in users
    ]
    return Response(data)


@login_required
def login_redirect(request):
    """Redireciona para a página correta baseado no perfil do usuário."""
    user = request.user

    # Voluntários/cabos vão direto pro campo mobile
    if user.role in ('volunteer', 'coordinator_neighborhood'):
        return redirect('/campo/')

    # Coordenadores municipais sem acesso ao dashboard vão pro campo
    if user.role == 'coordinator_city' and not user.has_module('dashboard'):
        return redirect('/campo/')

    # Todos os outros vão pro dashboard
    return redirect('/')
