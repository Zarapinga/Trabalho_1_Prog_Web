"""
URL configuration for planejamento project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import include, path

urlpatterns = [
    # As URLs do Grappelli devem vir ANTES das URLs do admin
    path("grappelli/", include("grappelli.urls")),
    path("admin/", admin.site.urls),
    # Área de autenticação e páginas do usuário final
    path("contas/", include("usuarios.urls")),
    # CRUD do domínio financeiro (Etapa C)
    path("financas/", include("financas.urls")),
]
