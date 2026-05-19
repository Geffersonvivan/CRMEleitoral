from django.contrib.auth.models import AbstractUser
from django.db import models


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

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.get_full_name() or self.username
