from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class ContaBancaria(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário", related_name="contas")
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

    def clean(self):
        super().clean()
        errors = {}

        if self.valor is not None and self.valor <= 0:
            errors['valor'] = "O valor de uma transação financeira deve ser estritamente maior que zero."

        if self.categoria_id and self.tipo:
            if self.categoria.tipo != self.tipo:
                errors['categoria'] = (
                    f"Inconsistência detectada! A categoria '{self.categoria.nome}' está configurada no sistema "
                    f"como {self.categoria.get_tipo_display()}, mas a transação foi marcada como "
                    f"{self.get_tipo_display()}. Os tipos devem coincidir."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.data} - {self.descricao} ({self.get_tipo_display()}: R$ {self.valor})"


class SimulacaoInvestimento(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuário", related_name="simulacoes")
    titulo = models.CharField("Título da Simulação", max_length=100, help_text="Ex: Aposentadoria, Compra de Carro")
    valor_inicial = models.DecimalField("Valor Inicial (R$)", max_digits=12, decimal_places=2)
    aporte_mensal = models.DecimalField("Aporte Mensal (R$)", max_digits=12, decimal_places=2, default=0.00)
    taxa_juros_anual = models.DecimalField("Taxa de Juros Anual (%)", max_digits=5, decimal_places=2)
    periodo_meses = models.IntegerField("Período (Meses)")
    data_criacao = models.DateTimeField("Data de Criação", auto_now_add=True)

    class Meta:
        verbose_name = "Simulação de Investimento"
        verbose_name_plural = "Simulações de Investimento"

    def clean(self):
        super().clean()
        errors = {}

        if self.valor_inicial is not None and self.valor_inicial < 0:
            errors['valor_inicial'] = "O aporte inicial não pode ser um valor negativo."

        if self.aporte_mensal is not None and self.aporte_mensal < 0:
            errors['aporte_mensal'] = "O aporte mensal não pode ser um valor negativo."

        if self.taxa_juros_anual is not None and self.taxa_juros_anual < 0:
            errors['taxa_juros_anual'] = "A taxa de juros anual não pode ser negativa."

        if self.periodo_meses is not None and self.periodo_meses <= 0:
            errors['periodo_meses'] = "O período da simulação deve ser de pelo menos 1 mês."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.titulo} - {self.periodo_meses} meses"