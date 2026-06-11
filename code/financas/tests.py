"""Testes da Etapa E — qualidade e segurança.

Cobertura:
  * Regras de negócio nos modelos (``Transacao.clean``,
    ``SimulacaoInvestimento.clean`` e ``SimulacaoInvestimento.calcular_montante``).
  * Isolamento por usuário nas views (cada usuário só acessa os próprios dados;
    acesso ao objeto de outro usuário resulta em 404; acesso anônimo redireciona
    para o login).
  * Dashboard: totais consolidados conferidos contra valores conhecidos.

Rodar com::

    .venv/bin/python manage.py test
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import PerfilUsuario

from .models import Categoria, ContaBancaria, SimulacaoInvestimento, Transacao


# ===========================================================================
# PARTE a — Regras de negócio nos modelos
# ===========================================================================
class TransacaoCleanTests(TestCase):
    """Validações de regra de negócio em ``Transacao.clean()``."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("dono", password="senha-forte-123")
        cls.conta = ContaBancaria.objects.create(
            usuario=cls.user, nome="Carteira", saldo_atual=Decimal("100.00")
        )
        cls.cat_receita = Categoria.objects.create(nome="Salário", tipo="RECEITA")
        cls.cat_despesa = Categoria.objects.create(nome="Mercado", tipo="DESPESA")

    def _transacao(self, **kwargs):
        dados = dict(
            descricao="Teste",
            valor=Decimal("10.00"),
            data=date(2026, 6, 1),
            conta=self.conta,
            categoria=self.cat_receita,
            tipo="RECEITA",
        )
        dados.update(kwargs)
        return Transacao(**dados)

    def test_valor_zero_levanta_validationerror(self):
        with self.assertRaises(ValidationError) as ctx:
            self._transacao(valor=Decimal("0.00")).clean()
        self.assertIn("valor", ctx.exception.message_dict)

    def test_valor_negativo_levanta_validationerror(self):
        with self.assertRaises(ValidationError) as ctx:
            self._transacao(valor=Decimal("-5.00")).clean()
        self.assertIn("valor", ctx.exception.message_dict)

    def test_tipo_divergente_da_categoria_levanta_validationerror(self):
        # Categoria de RECEITA, mas transação marcada como DESPESA.
        with self.assertRaises(ValidationError) as ctx:
            self._transacao(categoria=self.cat_receita, tipo="DESPESA").clean()
        self.assertIn("categoria", ctx.exception.message_dict)

    def test_transacao_valida_passa(self):
        # Não deve levantar exceção.
        self._transacao(categoria=self.cat_despesa, tipo="DESPESA").clean()
        self._transacao(categoria=self.cat_receita, tipo="RECEITA").clean()


class SimulacaoCleanTests(TestCase):
    """Validações de regra de negócio em ``SimulacaoInvestimento.clean()``."""

    def _sim(self, **kwargs):
        dados = dict(
            titulo="Aposentadoria",
            valor_inicial=Decimal("1000.00"),
            aporte_mensal=Decimal("100.00"),
            taxa_juros_anual=Decimal("10.00"),
            periodo_meses=12,
        )
        dados.update(kwargs)
        return SimulacaoInvestimento(**dados)

    def test_valor_inicial_negativo(self):
        with self.assertRaises(ValidationError) as ctx:
            self._sim(valor_inicial=Decimal("-1.00")).clean()
        self.assertIn("valor_inicial", ctx.exception.message_dict)

    def test_aporte_mensal_negativo(self):
        with self.assertRaises(ValidationError) as ctx:
            self._sim(aporte_mensal=Decimal("-1.00")).clean()
        self.assertIn("aporte_mensal", ctx.exception.message_dict)

    def test_taxa_juros_negativa(self):
        with self.assertRaises(ValidationError) as ctx:
            self._sim(taxa_juros_anual=Decimal("-1.00")).clean()
        self.assertIn("taxa_juros_anual", ctx.exception.message_dict)

    def test_periodo_menor_que_um(self):
        with self.assertRaises(ValidationError) as ctx:
            self._sim(periodo_meses=0).clean()
        self.assertIn("periodo_meses", ctx.exception.message_dict)

    def test_simulacao_valida_passa(self):
        self._sim().clean()


class CalcularMontanteTests(TestCase):
    """Testes do cálculo de juros compostos com aportes mensais."""

    def test_sem_juros_apenas_aportes(self):
        """Com taxa 0%, o montante é a soma simples de valor inicial + aportes."""
        sim = SimulacaoInvestimento(
            valor_inicial=Decimal("1000.00"),
            aporte_mensal=Decimal("100.00"),
            taxa_juros_anual=Decimal("0.00"),
            periodo_meses=12,
        )
        resultado = sim.calcular_montante()

        # 1000 + 100*12 = 2200
        self.assertEqual(resultado["total_aportado"], Decimal("2200.00"))
        self.assertEqual(resultado["montante_final"], Decimal("2200.00"))
        self.assertEqual(resultado["juros_ganhos"], Decimal("0.00"))

    def test_apenas_valor_inicial_com_juros(self):
        """Sem aportes, o montante é o valor inicial capitalizado.

        A 12,68% a.a. a taxa mensal equivalente é ~1% a.m., logo em 12 meses
        R$ 1.000 viram cerca de R$ 1.126,80.
        """
        sim = SimulacaoInvestimento(
            valor_inicial=Decimal("1000.00"),
            aporte_mensal=Decimal("0.00"),
            taxa_juros_anual=Decimal("12.68"),
            periodo_meses=12,
        )
        resultado = sim.calcular_montante()

        self.assertEqual(resultado["total_aportado"], Decimal("1000.00"))
        # Montante esperado ~ 1126.80; tolerância de R$ 0,10 pela conversão de taxa.
        self.assertAlmostEqual(
            float(resultado["montante_final"]), 1126.80, delta=0.10
        )
        self.assertGreater(resultado["juros_ganhos"], Decimal("0"))

    def test_apenas_aportes_com_juros(self):
        """Série de aportes mensais ao fim de cada mês, sem valor inicial.

        Com i_mensal ~ 1% a.m. (12,68% a.a.), o valor futuro de 12 aportes de
        R$ 100 é 100 * ((1.01**12 - 1) / 0.01) ≈ 1268,25 (calculado à mão).
        """
        sim = SimulacaoInvestimento(
            valor_inicial=Decimal("0.00"),
            aporte_mensal=Decimal("100.00"),
            taxa_juros_anual=Decimal("12.68"),
            periodo_meses=12,
        )
        resultado = sim.calcular_montante()

        self.assertEqual(resultado["total_aportado"], Decimal("1200.00"))
        self.assertAlmostEqual(
            float(resultado["montante_final"]), 1268.25, delta=0.20
        )

    def test_juros_e_aportes_juntos(self):
        """Montante final = principal capitalizado + valor futuro da série de aportes.

        Coerência: montante_final == total_aportado + juros_ganhos, e os juros
        são positivos quando há taxa > 0.
        """
        sim = SimulacaoInvestimento(
            valor_inicial=Decimal("500.00"),
            aporte_mensal=Decimal("200.00"),
            taxa_juros_anual=Decimal("10.00"),
            periodo_meses=24,
        )
        resultado = sim.calcular_montante()

        total_aportado = Decimal("500.00") + Decimal("200.00") * 24
        self.assertEqual(resultado["total_aportado"], total_aportado)
        self.assertGreater(resultado["juros_ganhos"], Decimal("0"))
        # Coerência da decomposição (com a tolerância de 1 centavo do arredondamento).
        self.assertAlmostEqual(
            float(resultado["montante_final"]),
            float(resultado["total_aportado"] + resultado["juros_ganhos"]),
            delta=0.01,
        )


# ===========================================================================
# PARTE b — Isolamento por usuário nas views
# ===========================================================================
class IsolamentoBase(TestCase):
    """Cria dois usuários (A e B), cada um com seus próprios dados."""

    SENHA = "senha-forte-123"

    @classmethod
    def setUpTestData(cls):
        cls.user_a = User.objects.create_user("alice", password=cls.SENHA)
        cls.user_b = User.objects.create_user("bob", password=cls.SENHA)

        cls.cat_receita = Categoria.objects.create(nome="Salário", tipo="RECEITA")
        cls.cat_despesa = Categoria.objects.create(nome="Mercado", tipo="DESPESA")

        # Dados do usuário A
        cls.conta_a = ContaBancaria.objects.create(
            usuario=cls.user_a, nome="NuConta A", saldo_atual=Decimal("500.00")
        )
        cls.transacao_a = Transacao.objects.create(
            descricao="Salário A",
            valor=Decimal("3000.00"),
            data=timezone.localdate(),
            conta=cls.conta_a,
            categoria=cls.cat_receita,
            tipo="RECEITA",
        )
        cls.simulacao_a = SimulacaoInvestimento.objects.create(
            usuario=cls.user_a,
            titulo="Sim A",
            valor_inicial=Decimal("1000.00"),
            aporte_mensal=Decimal("100.00"),
            taxa_juros_anual=Decimal("10.00"),
            periodo_meses=12,
        )

        # Dados do usuário B
        cls.conta_b = ContaBancaria.objects.create(
            usuario=cls.user_b, nome="NuConta B", saldo_atual=Decimal("800.00")
        )
        cls.transacao_b = Transacao.objects.create(
            descricao="Salário B",
            valor=Decimal("4000.00"),
            data=timezone.localdate(),
            conta=cls.conta_b,
            categoria=cls.cat_receita,
            tipo="RECEITA",
        )
        cls.simulacao_b = SimulacaoInvestimento.objects.create(
            usuario=cls.user_b,
            titulo="Sim B",
            valor_inicial=Decimal("2000.00"),
            aporte_mensal=Decimal("200.00"),
            taxa_juros_anual=Decimal("10.00"),
            periodo_meses=12,
        )

    def login_a(self):
        self.client.login(username="alice", password=self.SENHA)


class AcessoAnonimoTests(IsolamentoBase):
    """Acesso anônimo a páginas protegidas redireciona para o LOGIN_URL (302)."""

    def test_paginas_protegidas_redirecionam_para_login(self):
        login_url = reverse("usuarios:login")
        rotas = [
            reverse("financas:dashboard"),
            reverse("financas:conta_list"),
            reverse("financas:conta_create"),
            reverse("financas:conta_update", args=[self.conta_a.pk]),
            reverse("financas:conta_delete", args=[self.conta_a.pk]),
            reverse("financas:transacao_list"),
            reverse("financas:transacao_create"),
            reverse("financas:categoria_list"),
            reverse("financas:perfil_update"),
            reverse("financas:simulacao_list"),
            reverse("financas:simulacao_detail", args=[self.simulacao_a.pk]),
        ]
        for rota in rotas:
            with self.subTest(rota=rota):
                resp = self.client.get(rota)
                self.assertEqual(resp.status_code, 302)
                self.assertTrue(resp.url.startswith(login_url))


class ListViewIsolamentoTests(IsolamentoBase):
    """Logado como A, as ListViews mostram apenas os objetos de A."""

    def setUp(self):
        self.login_a()

    def test_conta_list_mostra_so_do_usuario(self):
        resp = self.client.get(reverse("financas:conta_list"))
        contas = list(resp.context["contas"])
        self.assertIn(self.conta_a, contas)
        self.assertNotIn(self.conta_b, contas)

    def test_transacao_list_mostra_so_do_usuario(self):
        resp = self.client.get(reverse("financas:transacao_list"))
        transacoes = list(resp.context["transacoes"])
        self.assertIn(self.transacao_a, transacoes)
        self.assertNotIn(self.transacao_b, transacoes)

    def test_simulacao_list_mostra_so_do_usuario(self):
        resp = self.client.get(reverse("financas:simulacao_list"))
        simulacoes = list(resp.context["simulacoes"])
        self.assertIn(self.simulacao_a, simulacoes)
        self.assertNotIn(self.simulacao_b, simulacoes)


class ObjetoDeOutroUsuario404Tests(IsolamentoBase):
    """Logado como A, acessar objeto de B (GET/POST) retorna 404 — nunca 200/403."""

    def setUp(self):
        self.login_a()

    # ---- Conta de B ----
    def test_get_update_conta_de_b_404(self):
        resp = self.client.get(reverse("financas:conta_update", args=[self.conta_b.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_post_update_conta_de_b_404(self):
        resp = self.client.post(
            reverse("financas:conta_update", args=[self.conta_b.pk]),
            {"nome": "Invadida", "saldo_atual": "0.00"},
        )
        self.assertEqual(resp.status_code, 404)
        # E não alterou o objeto de B.
        self.conta_b.refresh_from_db()
        self.assertEqual(self.conta_b.nome, "NuConta B")

    def test_get_delete_conta_de_b_404(self):
        resp = self.client.get(reverse("financas:conta_delete", args=[self.conta_b.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_post_delete_conta_de_b_404(self):
        resp = self.client.post(reverse("financas:conta_delete", args=[self.conta_b.pk]))
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(ContaBancaria.objects.filter(pk=self.conta_b.pk).exists())

    # ---- Transação de B ----
    def test_get_update_transacao_de_b_404(self):
        resp = self.client.get(
            reverse("financas:transacao_update", args=[self.transacao_b.pk])
        )
        self.assertEqual(resp.status_code, 404)

    def test_post_delete_transacao_de_b_404(self):
        resp = self.client.post(
            reverse("financas:transacao_delete", args=[self.transacao_b.pk])
        )
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Transacao.objects.filter(pk=self.transacao_b.pk).exists())

    # ---- Simulação de B ----
    def test_get_detail_simulacao_de_b_404(self):
        resp = self.client.get(
            reverse("financas:simulacao_detail", args=[self.simulacao_b.pk])
        )
        self.assertEqual(resp.status_code, 404)

    def test_get_update_simulacao_de_b_404(self):
        resp = self.client.get(
            reverse("financas:simulacao_update", args=[self.simulacao_b.pk])
        )
        self.assertEqual(resp.status_code, 404)

    def test_post_delete_simulacao_de_b_404(self):
        resp = self.client.post(
            reverse("financas:simulacao_delete", args=[self.simulacao_b.pk])
        )
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(
            SimulacaoInvestimento.objects.filter(pk=self.simulacao_b.pk).exists()
        )

    # ---- Objeto próprio (A) acessa normalmente (200) ----
    def test_proprio_objeto_acessa_200(self):
        resp = self.client.get(reverse("financas:conta_update", args=[self.conta_a.pk]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(
            reverse("financas:simulacao_detail", args=[self.simulacao_a.pk])
        )
        self.assertEqual(resp.status_code, 200)


class FormularioTransacaoIsolamentoTests(IsolamentoBase):
    """O campo ``conta`` lista só as contas do usuário; POST forjado é rejeitado."""

    def setUp(self):
        self.login_a()

    def test_queryset_de_conta_so_do_usuario(self):
        resp = self.client.get(reverse("financas:transacao_create"))
        form = resp.context["form"]
        contas_no_form = list(form.fields["conta"].queryset)
        self.assertIn(self.conta_a, contas_no_form)
        self.assertNotIn(self.conta_b, contas_no_form)

    def test_post_forjado_com_conta_de_b_e_rejeitado(self):
        """A tenta criar transação vinculada à conta de B via POST forjado."""
        resp = self.client.post(
            reverse("financas:transacao_create"),
            {
                "descricao": "Forjada",
                "valor": "50.00",
                "data": timezone.localdate().isoformat(),
                "conta": self.conta_b.pk,
                "categoria": self.cat_receita.pk,
                "tipo": "RECEITA",
            },
        )
        # Form inválido → re-renderiza (200) com erro no campo 'conta'.
        self.assertEqual(resp.status_code, 200)
        self.assertIn("conta", resp.context["form"].errors)
        # E nenhuma transação foi criada na conta de B.
        self.assertFalse(
            Transacao.objects.filter(descricao="Forjada", conta=self.conta_b).exists()
        )


class CreateAtribuiUsuarioTests(IsolamentoBase):
    """CreateView atribui ``usuario = request.user`` sem expor o campo."""

    def setUp(self):
        self.login_a()

    def test_create_conta_atribui_usuario_logado(self):
        resp = self.client.post(
            reverse("financas:conta_create"),
            {"nome": "Conta Nova A", "saldo_atual": "10.00"},
        )
        self.assertEqual(resp.status_code, 302)
        conta = ContaBancaria.objects.get(nome="Conta Nova A")
        self.assertEqual(conta.usuario, self.user_a)

    def test_form_conta_nao_expoe_usuario(self):
        resp = self.client.get(reverse("financas:conta_create"))
        self.assertNotIn("usuario", resp.context["form"].fields)

    def test_create_simulacao_atribui_usuario_logado(self):
        resp = self.client.post(
            reverse("financas:simulacao_create"),
            {
                "titulo": "Sim Nova A",
                "valor_inicial": "100.00",
                "aporte_mensal": "10.00",
                "taxa_juros_anual": "8.00",
                "periodo_meses": "6",
            },
        )
        self.assertEqual(resp.status_code, 302)
        sim = SimulacaoInvestimento.objects.get(titulo="Sim Nova A")
        self.assertEqual(sim.usuario, self.user_a)


class PerfilIsolamentoTests(IsolamentoBase):
    """A edição de perfil resolve o objeto pelo request.user, nunca por pk."""

    def setUp(self):
        self.login_a()

    def test_perfil_update_edita_proprio_perfil(self):
        resp = self.client.post(
            reverse("financas:perfil_update"),
            {"renda_mensal": "5000.00", "meta_patrimonio": "100000.00"},
        )
        self.assertEqual(resp.status_code, 302)
        perfil_a = PerfilUsuario.objects.get(user=self.user_a)
        self.assertEqual(perfil_a.meta_patrimonio, Decimal("100000.00"))
        # O perfil de B permanece intacto.
        perfil_b = PerfilUsuario.objects.get(user=self.user_b)
        self.assertEqual(perfil_b.meta_patrimonio, Decimal("0.00"))


# ===========================================================================
# PARTE c — Dashboard com dados conhecidos
# ===========================================================================
class DashboardTests(TestCase):
    """Confere os totais do dashboard contra valores calculados à mão."""

    SENHA = "senha-forte-123"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("carol", password=cls.SENHA)
        # Um intruso com dados que NÃO devem entrar nos totais de carol.
        cls.intruso = User.objects.create_user("dave", password=cls.SENHA)

        cls.cat_receita = Categoria.objects.create(nome="Salário", tipo="RECEITA")
        cls.cat_despesa = Categoria.objects.create(nome="Mercado", tipo="DESPESA")

        # Duas contas → saldo consolidado = 3000 + 2000 = 5000.
        conta1 = ContaBancaria.objects.create(
            usuario=cls.user, nome="C1", saldo_atual=Decimal("3000.00")
        )
        conta2 = ContaBancaria.objects.create(
            usuario=cls.user, nome="C2", saldo_atual=Decimal("2000.00")
        )

        hoje = timezone.localdate()
        # Receitas do mês: 4000. Despesas do mês: 1500. Saldo do mês: 2500.
        Transacao.objects.create(
            descricao="Salário", valor=Decimal("4000.00"), data=hoje,
            conta=conta1, categoria=cls.cat_receita, tipo="RECEITA",
        )
        Transacao.objects.create(
            descricao="Compras", valor=Decimal("1500.00"), data=hoje,
            conta=conta1, categoria=cls.cat_despesa, tipo="DESPESA",
        )
        # Transação de mês anterior — NÃO deve contar no mês corrente.
        mes_passado = (hoje.replace(day=1) - timezone.timedelta(days=1))
        Transacao.objects.create(
            descricao="Antiga", valor=Decimal("9999.00"), data=mes_passado,
            conta=conta1, categoria=cls.cat_receita, tipo="RECEITA",
        )

        # Dados do intruso — não devem aparecer nos totais de carol.
        conta_intruso = ContaBancaria.objects.create(
            usuario=cls.intruso, nome="X", saldo_atual=Decimal("99999.00")
        )
        Transacao.objects.create(
            descricao="Intruso", valor=Decimal("12345.00"), data=hoje,
            conta=conta_intruso, categoria=cls.cat_receita, tipo="RECEITA",
        )

        # Meta de patrimônio = 10000 → progresso = 5000/10000 = 50%.
        perfil = PerfilUsuario.objects.get(user=cls.user)
        perfil.meta_patrimonio = Decimal("10000.00")
        perfil.save()

    def test_dashboard_totais_conferem(self):
        self.client.login(username="carol", password=self.SENHA)
        resp = self.client.get(reverse("financas:dashboard"))
        ctx = resp.context

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ctx["saldo_total"], Decimal("5000.00"))
        self.assertEqual(ctx["receitas_mes"], Decimal("4000.00"))
        self.assertEqual(ctx["despesas_mes"], Decimal("1500.00"))
        self.assertEqual(ctx["saldo_mes"], Decimal("2500.00"))
        self.assertEqual(ctx["meta_patrimonio"], Decimal("10000.00"))
        self.assertAlmostEqual(ctx["progresso"], 50.0, delta=0.01)
        self.assertAlmostEqual(ctx["progresso_barra"], 50.0, delta=0.01)
