def user_permissions(request):
    """Injeta permissões do usuário no contexto dos templates."""
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {'user_modules': [], 'user_is_admin': False}

    return {
        'user_modules': request.user.get_modules(),
        'user_is_admin': request.user.is_admin(),
    }
