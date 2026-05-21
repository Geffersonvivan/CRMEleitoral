"""
Views para gestão de usuários: CRUD + API.
Somente admins podem acessar.
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User, MODULES, DEFAULT_MODULES
from apps.geography.models import Region


@login_required
def usuarios_page(request):
    """Página de gestão de usuários (só admin)."""
    if not request.user.has_module('usuarios'):
        return HttpResponseForbidden('Sem permissão')
    return render(request, 'accounts/usuarios.html')


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def usuarios_api(request):
    """Lista e criação de usuários."""
    if not request.user.has_module('usuarios'):
        return Response({'error': 'Sem permissão'}, status=403)

    if request.method == 'GET':
        qs = User.objects.select_related('city', 'region').order_by('first_name', 'last_name')

        # Filtros
        search = request.query_params.get('search', '')
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search) |
                Q(email__icontains=search)
            )

        role = request.query_params.get('role', '')
        if role:
            qs = qs.filter(role=role)

        active = request.query_params.get('is_active_campaign', '')
        if active == 'true':
            qs = qs.filter(is_active_campaign=True)
        elif active == 'false':
            qs = qs.filter(is_active_campaign=False)

        data = [_serialize_user(u) for u in qs]
        return Response(data)

    # POST - criar usuário
    return _create_or_update_user(request, user=None)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def usuario_detalhe_api(request, pk):
    """Detalhe, atualização e exclusão de usuário."""
    if not request.user.has_module('usuarios'):
        return Response({'error': 'Sem permissão'}, status=403)

    try:
        user = User.objects.select_related('city', 'region').get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'Usuário não encontrado'}, status=404)

    if request.method == 'GET':
        return Response(_serialize_user(user))

    if request.method == 'PATCH':
        return _create_or_update_user(request, user=user)

    if request.method == 'DELETE':
        user.is_active = False
        user.is_active_campaign = False
        user.save(update_fields=['is_active', 'is_active_campaign'])
        return Response({'ok': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def regioes_api(request):
    """Lista de regiões para selects."""
    regioes = Region.objects.all().order_by('name')
    data = [{'id': r.id, 'name': r.full_name or r.name} for r in regioes]
    return Response(data)


def _create_or_update_user(request, user=None):
    """Cria ou atualiza um usuário."""
    data = request.data
    errors = {}

    if not user:
        # Criação
        username = data.get('username', '').strip()
        if not username:
            errors['username'] = ['Usuário é obrigatório']
        elif User.objects.filter(username=username).exists():
            errors['username'] = ['Este usuário já existe']

        password = data.get('password', '')
        if not password or len(password) < 6:
            errors['password'] = ['Senha deve ter no mínimo 6 caracteres']

        if errors:
            return Response(errors, status=400)

        user = User.objects.create_user(
            username=username,
            password=password,
            email=data.get('email', ''),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
        )

    # Campos editáveis
    fields_to_update = []

    for field in ('first_name', 'last_name', 'email', 'phone', 'whatsapp', 'role', 'is_active_campaign'):
        if field in data:
            setattr(user, field, data[field])
            fields_to_update.append(field)

    if 'region' in data:
        user.region_id = data['region'] or None
        fields_to_update.append('region_id')

    if 'city' in data:
        user.city_id = data['city'] or None
        fields_to_update.append('city_id')

    if 'allowed_modules' in data:
        user.allowed_modules = data['allowed_modules'] or []
        fields_to_update.append('allowed_modules')

    if 'password' in data and data['password']:
        user.set_password(data['password'])
        fields_to_update.extend(['password'])

    if fields_to_update:
        user.save(update_fields=fields_to_update)

    return Response(_serialize_user(user), status=200 if request.method == 'PATCH' else 201)


def _serialize_user(user):
    """Serializa um User para JSON."""
    modules = user.get_modules()
    module_labels = {m[0]: m[1] for m in MODULES}

    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'phone': user.phone,
        'whatsapp': user.whatsapp,
        'role': user.role,
        'role_display': user.get_role_display(),
        'region': user.region_id,
        'region_name': user.region.name if user.region else '',
        'city': user.city_id,
        'city_name': user.city.name if user.city else '',
        'allowed_modules': user.allowed_modules or [],
        'modules_display': [module_labels.get(m, m) for m in modules],
        'is_active_campaign': user.is_active_campaign,
    }
