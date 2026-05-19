from django.db import models
from apps.core.models import TimeStampedModel


class Donation(TimeStampedModel):
    class Method(models.TextChoices):
        PIX = 'pix', 'PIX'
        TRANSFER = 'transfer', 'Transferência'
        CASH = 'cash', 'Espécie'
        CROWDFUNDING = 'crowdfunding', 'Financiamento Coletivo'

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

    class Meta:
        verbose_name = 'Doação'
        verbose_name_plural = 'Doações'
        ordering = ['-date']

    def __str__(self):
        return f'R${self.amount} - {self.donor}'


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
