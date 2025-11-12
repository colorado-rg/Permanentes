"""
URL configuration for permanentes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from core.views import RegisterView

urlpatterns = [
           path('admin/', admin.site.urls),
           # Inclui todas as URLs do app 'core'
           path('', include('core.urls')), 
           # Adiciona as páginas de login e logout nativas do Django
           path('contas/', include('django.contrib.auth.urls')), 
           path('contas/register/', RegisterView.as_view(), name='register'), 
    
       ]
