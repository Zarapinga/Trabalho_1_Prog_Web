from django.urls import path

from . import views

app_name = "financas"

urlpatterns = [
    # Dashboard (painel consolidado)
    path("painel/", views.DashboardView.as_view(), name="dashboard"),

    # Contas Bancárias
    path("contas-bancarias/", views.ContaListView.as_view(), name="conta_list"),
    path("contas-bancarias/nova/", views.ContaCreateView.as_view(), name="conta_create"),
    path("contas-bancarias/<int:pk>/editar/", views.ContaUpdateView.as_view(), name="conta_update"),
    path("contas-bancarias/<int:pk>/excluir/", views.ContaDeleteView.as_view(), name="conta_delete"),

    # Transações
    path("transacoes/", views.TransacaoListView.as_view(), name="transacao_list"),
    path("transacoes/nova/", views.TransacaoCreateView.as_view(), name="transacao_create"),
    path("transacoes/<int:pk>/editar/", views.TransacaoUpdateView.as_view(), name="transacao_update"),
    path("transacoes/<int:pk>/excluir/", views.TransacaoDeleteView.as_view(), name="transacao_delete"),

    # Categorias (catálogo global)
    path("categorias/", views.CategoriaListView.as_view(), name="categoria_list"),
    path("categorias/nova/", views.CategoriaCreateView.as_view(), name="categoria_create"),

    # Perfil financeiro
    path("perfil/", views.PerfilUpdateView.as_view(), name="perfil_update"),

    # Simulações de Investimento
    path("simulacoes/", views.SimulacaoListView.as_view(), name="simulacao_list"),
    path("simulacoes/nova/", views.SimulacaoCreateView.as_view(), name="simulacao_create"),
    path("simulacoes/<int:pk>/", views.SimulacaoDetailView.as_view(), name="simulacao_detail"),
    path("simulacoes/<int:pk>/editar/", views.SimulacaoUpdateView.as_view(), name="simulacao_update"),
    path("simulacoes/<int:pk>/excluir/", views.SimulacaoDeleteView.as_view(), name="simulacao_delete"),
]
