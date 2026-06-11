from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import RegistroForm


class RegistroView(CreateView):
    """Cadastro de um novo usuário final.

    Ao criar o User, o signal post_save gera automaticamente o PerfilUsuario.
    Após o cadastro, o usuário é autenticado e redirecionado para a área logada.
    """

    form_class = RegistroForm
    template_name = "usuarios/registro.html"
    success_url = reverse_lazy("usuarios:painel")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class PainelView(LoginRequiredMixin, TemplateView):
    """Página interna de exemplo, protegida por login.

    Serve para demonstrar o mecanismo de proteção (redireciona para o login
    quando o usuário não está autenticado). As telas de negócio reais virão
    nas próximas etapas do Checkpoint 2.
    """

    template_name = "usuarios/painel.html"
