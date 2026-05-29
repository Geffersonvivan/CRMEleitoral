from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Captador


def public_doar_page(request, slug):
    """Página pública de doação — sem login."""
    get_object_or_404(Captador, slug=slug, is_active=True)
    return render(request, 'fundraising/public_doar.html', {'slug': slug})


@login_required
def captadores_page(request):
    return render(request, 'fundraising/captadores.html')


@login_required
def rede_page(request):
    return render(request, 'fundraising/rede.html')
