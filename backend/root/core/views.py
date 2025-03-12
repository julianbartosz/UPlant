# backend/root/core/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
    return render(request, 'core/home.html')


@login_required
def search_select(request):
    return render(request, 'core/search_select.html')
