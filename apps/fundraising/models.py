import secrets
import string

from django.db import models
from django.conf import settings

from apps.core.models import TimeStampedModel


class Captador(TimeStampedModel):
    class Tipo(models.TextChoices):
        COORDENADOR = 'coordenador', 'Coordenador'
        APOIADOR = 'apoiador', 'Apoiador'

    contact = models.OneToOneField(
        'contacts.Contact', verbose_name='Contato',
        on_delete=models.CASCADE, related_name='captador'
    )
    tipo = models.CharField('Tipo', max_length=20, choices=Tipo.choices, db_index=True)
    coordenador = models.ForeignKey(
        'self', verbose_name='Coordenador responsável',
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='apoiadores',
        limit_choices_to={'tipo': 'coordenador'}
    )
    slug = models.SlugField('Código único', max_length=12, unique=True, db_index=True)
    qrcode_image = models.ImageField(
        'QR Code', upload_to='fundraising/qrcodes/', blank=True
    )
    is_active = models.BooleanField('Ativo', default=True)
    saldo_disponivel = models.DecimalField(
        'Saldo disponível', max_digits=10, decimal_places=2, default=0
    )
    total_arrecadado = models.DecimalField(
        'Total arrecadado', max_digits=10, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = 'Captador'
        verbose_name_plural = 'Captadores'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_tipo_display()}: {self.contact.full_name}'

    def get_link(self):
        return f'/doar/{self.slug}/'

    def get_absolute_url(self):
        return f'{settings.SITE_URL}/doar/{self.slug}/'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def generate_qrcode(self):
        from .qrcode_utils import generate_qrcode_for_url
        url = self.get_absolute_url()
        content = generate_qrcode_for_url(url)
        filename = f'qr_{self.slug}.png'
        self.qrcode_image.save(filename, content, save=True)

    @staticmethod
    def _generate_unique_slug():
        chars = string.ascii_lowercase + string.digits
        while True:
            slug = ''.join(secrets.choice(chars) for _ in range(8))
            if not Captador.objects.filter(slug=slug).exists():
                return slug


class Donation(TimeStampedModel):
    class Method(models.TextChoices):
        PIX = 'pix', 'PIX'
        TRANSFER = 'transfer', 'Transferência'
        CASH = 'cash', 'Espécie'
        CROWDFUNDING = 'crowdfunding', 'Financiamento Coletivo'
        ONLINE = 'online', 'Doação Online'

    class PixStatus(models.TextChoices):
        PENDING = 'pending', 'Aguardando'
        PAID = 'paid', 'Pago'
        EXPIRED = 'expired', 'Expirado'
        CANCELLED = 'cancelled', 'Cancelado'

    donor = models.ForeignKey(
        'contacts.Contact', verbose_name='Doador',
        on_delete=models.SET_NULL, null=True, related_name='donations'
    )
    amount = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    date = models.DateField('Data')
    receipt_number = models.CharField('Número do recibo', max_length=100, blank=True)
    method = models.CharField('Método', max_length=30, choices=Method.choices)
    is_verified = models.BooleanField('Verificado', default=False)
    notes = models.TextField('Observações', blank=True)

    # Rede de captação
    captador = models.ForeignKey(
        Captador, verbose_name='Captador',
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name='doacoes_captadas'
    )
    donor_cpf = models.CharField('CPF do doador', max_length=14, blank=True, db_index=True)
    donor_name = models.CharField('Nome do doador', max_length=255, blank=True)
    donor_phone = models.CharField('Telefone do doador', max_length=20, blank=True)

    # PIX
    pix_txid = models.CharField(
        'PIX TXID', max_length=100, blank=True, null=True, unique=True, default=None
    )
    pix_status = models.CharField(
        'Status PIX', max_length=20, blank=True,
        choices=PixStatus.choices
    )

    # Comissões
    comissao_plataforma = models.DecimalField(
        'Comissão plataforma (10%)', max_digits=10, decimal_places=2, default=0
    )
    comissao_coordenador = models.DecimalField(
        'Comissão coordenador (7%)', max_digits=10, decimal_places=2, default=0
    )
    comissao_apoiador = models.DecimalField(
        'Comissão apoiador (3%)', max_digits=10, decimal_places=2, default=0
    )
    valor_candidato = models.DecimalField(
        'Valor candidato (80%)', max_digits=10, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = 'Doação'
        verbose_name_plural = 'Doações'
        ordering = ['-date']

    def __str__(self):
        return f'R${self.amount} - {self.donor}'

    def calcular_comissoes(self):
        from decimal import Decimal
        self.comissao_plataforma = self.amount * Decimal('0.10')
        self.comissao_coordenador = self.amount * Decimal('0.07')
        self.comissao_apoiador = self.amount * Decimal('0.03')
        self.valor_candidato = self.amount * Decimal('0.80')


class Expense(TimeStampedModel):
    description = models.CharField('Descrição', max_length=255)
    amount = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    date = models.DateField('Data')
    category = models.CharField('Categoria', max_length=50)
    receipt = models.FileField('Recibo', upload_to='expenses/receipts/', blank=True)
    approved_by = models.ForeignKey(
        'accounts.User', verbose_name='Aprovado por',
        null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'
        ordering = ['-date']

    def __str__(self):
        return f'{self.description} - R${self.amount}'


class SolicitacaoResgate(TimeStampedModel):
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        APROVADO = 'aprovado', 'Aprovado'
        PAGO = 'pago', 'Pago'
        REJEITADO = 'rejeitado', 'Rejeitado'

    captador = models.ForeignKey(
        Captador, verbose_name='Captador',
        on_delete=models.CASCADE, related_name='resgates'
    )
    valor = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    status = models.CharField(
        'Status', max_length=20, choices=Status.choices, default=Status.PENDENTE
    )
    nota_fiscal = models.FileField(
        'Nota Fiscal', upload_to='fundraising/notas_fiscais/', blank=True
    )
    dados_bancarios = models.JSONField('Dados bancários', default=dict, blank=True)
    observacoes = models.TextField('Observações', blank=True)
    aprovado_por = models.ForeignKey(
        'accounts.User', verbose_name='Aprovado por',
        null=True, blank=True, on_delete=models.SET_NULL
    )
    data_pagamento = models.DateField('Data do pagamento', null=True, blank=True)

    class Meta:
        verbose_name = 'Solicitação de Resgate'
        verbose_name_plural = 'Solicitações de Resgate'
        ordering = ['-created_at']

    def __str__(self):
        return f'R${self.valor} - {self.captador} ({self.get_status_display()})'
