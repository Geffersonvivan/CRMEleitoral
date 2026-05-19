from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def elections_dashboard(request):
    return render(request, 'elections/dashboard.html')
