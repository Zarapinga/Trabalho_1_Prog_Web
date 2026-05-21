from django.db import models
from django.core.exceptions import ValidationError


class ContaBancaria(models.Model):
    nome = models.CharField("Nome da Conta", max_length=100, help_text="Ex: NuConta, Carteira, Bradesco")
    saldo_atual = models.DecimalField("Saldo Atual (R$)", max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"

    def __str__(self):
        return f"{self.nome} (R$ {self.saldo_atual})"


class Categoria(models.Model):
    TIPO_CHOICES = [
        ('RECEITA', 'Receita (Entrada)'),
        ('DESPESA', 'Despesa (Saída)'),
    ]

    nome = models.CharField("Nome da Categoria", max_length=100, help_text="Ex: Alimentação, Salário, Investimentos")
    tipo = models.CharField("Tipo", max_length=10, choices=TIPO_CHOICES)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class Transacao(models.Model):
    TIPO_CHOICES = [
        ('RECEITA', 'Receita'),
        ('DESPESA', 'Despesa'),
    ]

    descricao = models.CharField("Descrição", max_length=255)
    valor = models.DecimalField("Valor (R$)", max_digits=12, decimal_places=2)
    data = models.DateField("Data da Transação")
    conta = models.ForeignKey(ContaBancaria, db_index=True, on_delete=models.CASCADE, verbose_name="Conta Bancária")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, verbose_name="Categoria")
    tipo = models.CharField("Tipo", max_length=10, choices=TIPO_CHOICES)

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"

    def __str__(self):
        return f"{self.data} - {self.descricao} ({self.get_tipo_display()}: R$ {self.valor})"


class SimulacaoInvestimento(models.Model):
    titulo = models.CharField("Título da Simulação", max_length=100, help_text="Ex: Aposentadoria, Compra de Carro")
    valor_inicial = models.DecimalField("Valor Inicial (R$)", max_digits=12, decimal_places=2)
    aporte_mensal = models.DecimalField("Aporte Mensal (R$)", max_digits=12, decimal_places=2, default=0.00)
    taxa_juros_anual = models.DecimalField("Taxa de Juros Anual (%)", max_digits=5, decimal_places=2)
    periodo_meses = models.IntegerField("Período (Meses)")
    data_criacao = models.DateTimeField("Data de Criação", auto_now_add=True)

    class Meta:
        verbose_name = "Simulação de Investimento"
        verbose_name_plural = "Simulações de Investimento"

    def __str__(self):
        return f"{self.titulo} - {self.periodo_meses} meses"