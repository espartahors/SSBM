"""
URL configuration for SSBModel project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SSBModel.settings')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='parts/', permanent=False)),  # Redirect root to parts
    path('users/', include('users.urls')),
    path('parts/', include('parts.urls')),
    path('equipment/', include('equipment.urls')),
    path('catalog/', include('catalog.urls')),
]

# Add URL patterns for media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
