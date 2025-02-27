# parts/views_codification.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

@login_required
@ensure_csrf_cookie
def codification_viewer(request):
    """View for the equipment codification tree viewer"""
    context = {
        'title': 'Equipment Codification Viewer'
    }
    return render(request, 'parts/codification_viewer.html', context)