# backend/root/core/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
    return render(request, 'core/home.html')
    # return render(request, 'core/home.html', {'test_message': 'BACKEND HOME PAGE - DJANGO'})

@login_required
def search_select(request):
    return render(request, 'core/search_select.html')


def about(request):
    return render(request, 'core/about.html')


def privacy(request):
    return render(request, 'core/privacy.html')


def help_page(request):
    return render(request, 'core/help.html')


def terms(request):
    return render(request, 'core/terms.html')


def contact(request):
    return render(request, 'core/contact.html')