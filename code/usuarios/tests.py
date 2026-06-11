"""Testes do app ``usuarios`` (Etapa E).

Cobre o signal que cria o ``PerfilUsuario`` automaticamente e a proteção por
login das páginas do usuário final.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import PerfilUsuario


class SignalPerfilTests(TestCase):
    """O signal post_save cria um PerfilUsuario para cada User criado."""

    def test_perfil_criado_automaticamente(self):
        user = User.objects.create_user("novo", password="senha-forte-123")
        self.assertTrue(PerfilUsuario.objects.filter(user=user).exists())


class AcessoPainelTests(TestCase):
    """A página do painel é protegida por login (302 -> LOGIN_URL)."""

    def test_painel_anonimo_redireciona_para_login(self):
        resp = self.client.get(reverse("usuarios:painel"))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith(reverse("usuarios:login")))

    def test_painel_logado_200(self):
        User.objects.create_user("logado", password="senha-forte-123")
        self.client.login(username="logado", password="senha-forte-123")
        resp = self.client.get(reverse("usuarios:painel"))
        self.assertEqual(resp.status_code, 200)
