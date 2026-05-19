from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def campaign_list(request):
    return render(request, 'campaigns/list.html')


@login_required
def kanban_view(request):
    return render(request, 'campaigns/kanban.html')


@login_required
def itinerary_list(request):
    return render(request, 'campaigns/itineraries.html')


@login_required
def itinerary_detail(request, pk):
    return render(request, 'campaigns/itinerary_detail.html', {'itinerary_id': pk})


@login_required
def content_list(request):
    return render(request, 'campaigns/contents.html')
