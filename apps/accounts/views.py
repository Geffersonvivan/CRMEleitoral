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
