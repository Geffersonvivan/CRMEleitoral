from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Contact, CompanyPartner


@login_required
def contact_list(request):
    return render(request, 'contacts/list.html')


@login_required
def contact_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    return render(request, 'contacts/detail.html', {'contact_id': pk})


@login_required
def company_list(request):
    return render(request, 'contacts/companies.html')
