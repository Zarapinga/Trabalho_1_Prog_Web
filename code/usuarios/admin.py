from django.contrib import admin
from .models import PerfilUsuario


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'renda_mensal', 'meta_patrimonio', 'data_atualizacao')
    search_fields = ('user__username',)
    list_filter = ('data_atualizacao',)
