from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def event_list(request):
    return render(request, 'events/list.html')
