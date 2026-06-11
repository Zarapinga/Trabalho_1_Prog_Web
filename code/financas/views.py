from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from usuarios.models import PerfilUsuario

from .forms import (
    CategoriaForm,
    ContaBancariaForm,
    PerfilUsuarioForm,
    SimulacaoInvestimentoForm,
    TransacaoForm,
)
from .models import Categoria, ContaBancaria, SimulacaoInvestimento, Transacao


class MensagemCreateMixin:
    """Adiciona uma mensagem de sucesso após a criação."""

    mensagem_sucesso = "Registro criado com sucesso."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.mensagem_sucesso)
        return response


class MensagemUpdateMixin:
    """Adiciona uma mensagem de sucesso após a edição."""

    mensagem_sucesso = "Registro atualizado com sucesso."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.mensagem_sucesso)
        return response


# ---------------------------------------------------------------------------
# Contas Bancárias
# ---------------------------------------------------------------------------
class ContaListView(LoginRequiredMixin, ListView):
    model = ContaBancaria
    template_name = "financas/conta_list.html"
    context_object_name = "contas"

    def get_queryset(self):
        return ContaBancaria.objects.filter(usuario=self.request.user)


class ContaCreateView(LoginRequiredMixin, MensagemCreateMixin, CreateView):
    model = ContaBancaria
    form_class = ContaBancariaForm
    template_name = "financas/conta_form.html"
    success_url = reverse_lazy("financas:conta_list")
    mensagem_sucesso = "Conta bancária criada com sucesso."

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class ContaUpdateView(LoginRequiredMixin, MensagemUpdateMixin, UpdateView):
    model = ContaBancaria
    form_class = ContaBancariaForm
    template_name = "financas/conta_form.html"
    success_url = reverse_lazy("financas:conta_list")
    mensagem_sucesso = "Conta bancária atualizada com sucesso."

    def get_queryset(self):
        return ContaBancaria.objects.filter(usuario=self.request.user)


class ContaDeleteView(LoginRequiredMixin, DeleteView):
    model = ContaBancaria
    template_name = "financas/conta_confirm_delete.html"
    success_url = reverse_lazy("financas:conta_list")

    def get_queryset(self):
        return ContaBancaria.objects.filter(usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Conta bancária excluída com sucesso.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Transações
# ---------------------------------------------------------------------------
class TransacaoListView(LoginRequiredMixin, ListView):
    model = Transacao
    template_name = "financas/transacao_list.html"
    context_object_name = "transacoes"

    def get_queryset(self):
        return (
            Transacao.objects.filter(conta__usuario=self.request.user)
            .select_related("conta", "categoria")
            .order_by("-data")
        )


class TransacaoCreateView(LoginRequiredMixin, MensagemCreateMixin, CreateView):
    model = Transacao
    form_class = TransacaoForm
    template_name = "financas/transacao_form.html"
    success_url = reverse_lazy("financas:transacao_list")
    mensagem_sucesso = "Transação criada com sucesso."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs


class TransacaoUpdateView(LoginRequiredMixin, MensagemUpdateMixin, UpdateView):
    model = Transacao
    form_class = TransacaoForm
    template_name = "financas/transacao_form.html"
    success_url = reverse_lazy("financas:transacao_list")
    mensagem_sucesso = "Transação atualizada com sucesso."

    def get_queryset(self):
        return Transacao.objects.filter(conta__usuario=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["usuario"] = self.request.user
        return kwargs


class TransacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = Transacao
    template_name = "financas/transacao_confirm_delete.html"
    success_url = reverse_lazy("financas:transacao_list")

    def get_queryset(self):
        return Transacao.objects.filter(conta__usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Transação excluída com sucesso.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Categorias (catálogo global — ver DOCUMENTACAO.md, seção 7.2 Etapa C)
# ---------------------------------------------------------------------------
class CategoriaListView(LoginRequiredMixin, ListView):
    model = Categoria
    template_name = "financas/categoria_list.html"
    context_object_name = "categorias"
    ordering = ("tipo", "nome")


class CategoriaCreateView(LoginRequiredMixin, MensagemCreateMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "financas/categoria_form.html"
    success_url = reverse_lazy("financas:categoria_list")
    mensagem_sucesso = "Categoria criada com sucesso."


# ---------------------------------------------------------------------------
# Perfil financeiro
# ---------------------------------------------------------------------------
class PerfilUpdateView(LoginRequiredMixin, MensagemUpdateMixin, UpdateView):
    model = PerfilUsuario
    form_class = PerfilUsuarioForm
    template_name = "financas/perfil_form.html"
    success_url = reverse_lazy("usuarios:painel")
    mensagem_sucesso = "Perfil financeiro atualizado com sucesso."

    def get_object(self, queryset=None):
        # O PerfilUsuario é criado pelo signal no cadastro; get_or_create
        # protege contra usuários antigos que ainda não o tenham.
        perfil, _ = PerfilUsuario.objects.get_or_create(user=self.request.user)
        return perfil


# ---------------------------------------------------------------------------
# Dashboard (painel consolidado do usuário autenticado)
# ---------------------------------------------------------------------------
class DashboardView(LoginRequiredMixin, TemplateView):
    """Resumo financeiro consolidado, calculado apenas sobre os dados do usuário.

    Todos os agregados usam ``Sum`` do ORM (sem laços Python) e são filtrados
    estritamente por ``request.user``.
    """

    template_name = "financas/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user

        # 1. Saldo total consolidado = soma dos saldos de todas as contas.
        saldo_total = (
            ContaBancaria.objects.filter(usuario=usuario).aggregate(
                total=Sum("saldo_atual")
            )["total"]
            or Decimal("0.00")
        )

        # 2. Receitas e Despesas do mês corrente (agregação por tipo).
        hoje = timezone.localdate()
        transacoes_mes = Transacao.objects.filter(
            conta__usuario=usuario,
            data__year=hoje.year,
            data__month=hoje.month,
        )
        receitas_mes = (
            transacoes_mes.filter(tipo="RECEITA").aggregate(total=Sum("valor"))["total"]
            or Decimal("0.00")
        )
        despesas_mes = (
            transacoes_mes.filter(tipo="DESPESA").aggregate(total=Sum("valor"))["total"]
            or Decimal("0.00")
        )

        # 3. Saldo do mês.
        saldo_mes = receitas_mes - despesas_mes

        # 4. Progresso rumo à meta de patrimônio (trata meta = 0).
        perfil, _ = PerfilUsuario.objects.get_or_create(user=usuario)
        meta = perfil.meta_patrimonio or Decimal("0.00")
        if meta > 0:
            progresso = (saldo_total / meta) * Decimal("100")
            progresso = round(float(progresso), 1)
        else:
            progresso = 0.0
        # Largura da barra limitada a 100% (o percentual textual pode exceder).
        progresso_barra = min(progresso, 100.0)

        context.update(
            {
                "saldo_total": saldo_total,
                "receitas_mes": receitas_mes,
                "despesas_mes": despesas_mes,
                "saldo_mes": saldo_mes,
                "meta_patrimonio": meta,
                "progresso": progresso,
                "progresso_barra": progresso_barra,
                "mes_referencia": hoje,
            }
        )
        return context


# ---------------------------------------------------------------------------
# Simulações de Investimento
# ---------------------------------------------------------------------------
class SimulacaoListView(LoginRequiredMixin, ListView):
    model = SimulacaoInvestimento
    template_name = "financas/simulacao_list.html"
    context_object_name = "simulacoes"

    def get_queryset(self):
        return SimulacaoInvestimento.objects.filter(
            usuario=self.request.user
        ).order_by("-data_criacao")


class SimulacaoDetailView(LoginRequiredMixin, DetailView):
    model = SimulacaoInvestimento
    template_name = "financas/simulacao_detail.html"
    context_object_name = "simulacao"

    def get_queryset(self):
        return SimulacaoInvestimento.objects.filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resultado"] = self.object.calcular_montante()
        return context


class SimulacaoCreateView(LoginRequiredMixin, MensagemCreateMixin, CreateView):
    model = SimulacaoInvestimento
    form_class = SimulacaoInvestimentoForm
    template_name = "financas/simulacao_form.html"
    mensagem_sucesso = "Simulação criada com sucesso."

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("financas:simulacao_detail", kwargs={"pk": self.object.pk})


class SimulacaoUpdateView(LoginRequiredMixin, MensagemUpdateMixin, UpdateView):
    model = SimulacaoInvestimento
    form_class = SimulacaoInvestimentoForm
    template_name = "financas/simulacao_form.html"
    mensagem_sucesso = "Simulação atualizada com sucesso."

    def get_queryset(self):
        return SimulacaoInvestimento.objects.filter(usuario=self.request.user)

    def get_success_url(self):
        return reverse_lazy("financas:simulacao_detail", kwargs={"pk": self.object.pk})


class SimulacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = SimulacaoInvestimento
    template_name = "financas/simulacao_confirm_delete.html"
    success_url = reverse_lazy("financas:simulacao_list")

    def get_queryset(self):
        return SimulacaoInvestimento.objects.filter(usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Simulação excluída com sucesso.")
        return super().form_valid(form)
