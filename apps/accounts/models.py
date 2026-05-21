from django.contrib.auth.models import AbstractUser
from django.db import models


# Módulos disponíveis no CRM
MODULES = [
    ('dashboard', 'Dashboard'),
    ('contatos', 'Contatos'),
    ('eventos', 'Eventos'),
    ('campanhas', 'Campanhas/Demandas'),
    ('mapas', 'Mapas'),
    ('eleicoes', 'Eleições'),
    ('comunicacoes', 'Comunicações'),
    ('financeiro', 'Financeiro'),
    ('campo', 'Campo Mobile'),
    ('usuarios', 'Gestão de Usuários'),
]

# Módulos padrão por perfil
DEFAULT_MODULES = {
    'admin': [m[0] for m in MODULES],
    'coordinator_state': ['dashboard', 'contatos', 'eventos', 'campanhas', 'mapas', 'eleicoes', 'comunicacoes', 'campo'],
    'coordinator_region': ['dashboard', 'contatos', 'eventos', 'campanhas', 'mapas', 'campo'],
    'coordinator_city': ['dashboard', 'contatos', 'eventos', 'campo'],
    'coordinator_neighborhood': ['contatos', 'eventos', 'campo'],
    'volunteer': ['campo'],
    'viewer': ['dashboard', 'mapas', 'eleicoes'],
}


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        COORD_STATE = 'coordinator_state', 'Coordenador Estadual'
        COORD_REGION = 'coordinator_region', 'Coordenador Regional'
        COORD_CITY = 'coordinator_city', 'Coordenador Municipal'
        COORD_NEIGHBORHOOD = 'coordinator_neighborhood', 'Coordenador de Bairro'
        VOLUNTEER = 'volunteer', 'Voluntário'
        VIEWER = 'viewer', 'Visualizador'

    role = models.CharField('Função', max_length=30, choices=Role.choices, default=Role.VIEWER)
    phone = models.CharField('Telefone', max_length=20, blank=True)
    whatsapp = models.CharField('WhatsApp', max_length=20, blank=True)
    city = models.ForeignKey(
        'geography.City', verbose_name='Cidade',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    region = models.ForeignKey(
        'geography.Region', verbose_name='Região',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    photo = models.ImageField('Foto', upload_to='users/photos/', blank=True)
    is_active_campaign = models.BooleanField('Ativo na campanha', default=True)
    allowed_modules = models.JSONField(
        'Módulos permitidos', default=list, blank=True,
        help_text='Lista de módulos que o usuário pode acessar. Vazio = usa padrão do perfil.',
    )

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.get_full_name() or self.username

    def get_modules(self):
        """Retorna módulos permitidos (custom ou padrão do perfil)."""
        if self.allowed_modules:
            return self.allowed_modules
        return DEFAULT_MODULES.get(self.role, [])

    def has_module(self, module):
        """Verifica se o usuário tem acesso a um módulo."""
        if self.role == 'admin':
            return True
        return module in self.get_modules()

    def is_admin(self):
        return self.role == 'admin'

    def is_territorial(self):
        """Retorna True se o usuário tem filtro territorial (não é admin/estadual)."""
        return self.role not in ('admin', 'coordinator_state')

    def get_territory_filter(self):
        """Retorna dict para filtrar querysets pelo território do usuário."""
        if not self.is_territorial():
            return {}
        if self.role == 'coordinator_city' or self.role == 'coordinator_neighborhood':
            if self.city_id:
                return {'city_id': self.city_id}
        if self.region_id:
            return {'region_id': self.region_id}
        return {}
