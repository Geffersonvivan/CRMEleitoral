"""
Middleware de permissões e filtro territorial.
Injeta dados de permissão no request e bloqueia acesso a módulos não autorizados.
"""
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.conf import settings

# Mapeamento URL prefix -> módulo
URL_MODULE_MAP = {
    '/': 'dashboard',
    '/contatos/': 'contatos',
    '/eventos/': 'eventos',
    '/campanhas/': 'campanhas',
    '/demandas/': 'campanhas',
    '/roteiros/': 'campanhas',
    '/conteudos/': 'campanhas',
    '/eleicoes/': 'eleicoes',
    '/campo/': 'campo',
    '/usuarios/': 'usuarios',
    # APIs seguem o módulo correspondente
    '/api/v1/contacts/': 'contatos',
    '/api/v1/events/': 'eventos',
    '/api/v1/campaigns/': 'campanhas',
    '/api/v1/elections/': 'eleicoes',
    '/api/v1/communications/': 'comunicacoes',
    '/api/v1/fundraising/': 'financeiro',
    '/api/v1/campo/': 'campo',
    '/api/v1/dashboard/': 'dashboard',
    '/api/v1/maps/': 'mapas',
    '/api/v1/geo/': 'mapas',
    '/api/v1/accounts/users/': 'usuarios',
}

# URLs que não precisam de verificação de módulo
EXEMPT_PREFIXES = (
    '/admin/',
    '/accounts/',
    '/static/',
    '/media/',
)


class TerritoryMiddleware:
    """
    Middleware que:
    1. Injeta request.user_modules, request.user_territory
    2. Bloqueia acesso a módulos não autorizados
    3. Redireciona por perfil após login
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Pular para URLs isentas
        if any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return self.get_response(request)

        # Usuário não autenticado -> deixar o LoginRequired tratar
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return self.get_response(request)

        user = request.user

        # Injetar dados no request
        request.user_modules = user.get_modules()
        request.user_territory = user.get_territory_filter()
        request.user_is_admin = user.is_admin()

        # Verificar permissão de módulo
        module = self._get_module(path)
        if module and not user.has_module(module):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return HttpResponseForbidden('{"error": "Sem permissão"}', content_type='application/json')
            return HttpResponseRedirect(self._get_home_url(user))

        return self.get_response(request)

    def _get_module(self, path):
        """Determina qual módulo corresponde ao path."""
        # Checar prefixos mais específicos primeiro (mais longos)
        for prefix in sorted(URL_MODULE_MAP.keys(), key=len, reverse=True):
            if path.startswith(prefix) and prefix != '/':
                return URL_MODULE_MAP[prefix]
        # Home (/) só match exato
        if path == '/':
            return 'dashboard'
        return None

    def _get_home_url(self, user):
        """URL inicial baseada no perfil do usuário."""
        if user.role == 'volunteer':
            return '/campo/'
        if user.has_module('dashboard'):
            return '/'
        if user.has_module('campo'):
            return '/campo/'
        return '/'
