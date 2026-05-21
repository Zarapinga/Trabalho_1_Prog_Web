from django.contrib import admin
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin, TabularInline
from .models import ContaBancaria, Categoria, Transacao, SimulacaoInvestimento


# 1. Configuração do Inline
class TransacaoInline(TabularInline):
    """Permite visualizar e criar transações diretamente na tela da Conta Bancária."""
    model = Transacao
    extra = 1  # Quantidade de linhas em branco exibidas para inserção rápida
    fields = ('data', 'descricao', 'tipo', 'categoria', 'valor')


# 2. Customização do painel de Contas Bancárias
@admin.register(ContaBancaria)
class ContaBancariaAdmin(ModelAdmin):
    list_display = ('nome', 'saldo_atual')
    search_fields = ('nome',)
    inlines = [TransacaoInline] 


# 3. Customização do painel de Categorias
@admin.register(Categoria)
class CategoriaAdmin(ModelAdmin):
    list_display = ('nome', 'tipo')
    list_filter = ('tipo',)
    search_fields = ('nome',)


# 4. Customização do painel de Transações (Foco nas validações e filtros complexos)
@admin.register(Transacao)
class TransacaoAdmin(ModelAdmin):
    list_display = ('data', 'descricao', 'conta', 'categoria', 'tipo', 'valor')
    list_filter = ('tipo', 'conta', 'categoria', 'data')
    search_fields = ('descricao',)

    # Exigência do Professor: Implementação do método clean customizado para validação no Admin
    def clean_form(self, form, change):
        """
        Método de validação do Unfold equivalente ao clean do ModelAdmin clássico.
        Garante consistência antes de salvar os registros via interface administrativa.
        """
        cleaned_data = form.cleaned_data
        valor = cleaned_data.get('valor')
        tipo = cleaned_data.get('tipo')
        categoria = cleaned_data.get('categoria')

        # Validação 1: Bloqueia valores negativos ou nulos
        if valor is not None and valor <= 0:
            raise ValidationError({
                'valor': "O valor de uma transação financeira deve ser estritamente maior que zero."
            })

        # Validação 2: Validação cruzada (Regra de Negócio)
        # Impede que o usuário associe uma categoria de DESPESA a uma transação marcada como RECEITA
        if categoria and tipo:
            if categoria.tipo != tipo:
                raise ValidationError(
                    f"Inconsistência detectada! A categoria '{categoria.nome}' está configurada no sistema "
                    f"como {categoria.get_tipo_display()}, mas a transação foi marcada como {tipo}. "
                    f"Os tipos devem coincidir."
                )


# 5. Customização do painel de Simulações
@admin.register(SimulacaoInvestimento)
class SimulacaoInvestimentoAdmin(ModelAdmin):
    list_display = ('titulo', 'valor_inicial', 'aporte_mensal', 'taxa_juros_anual', 'periodo_meses', 'data_criacao')
    list_filter = ('data_criacao', 'periodo_meses')
    search_fields = ('titulo',)

    def clean_form(self, form, change):
        cleaned_data = form.cleaned_data
        valor_inicial = cleaned_data.get('valor_inicial')
        periodo_meses = cleaned_data.get('periodo_meses')

        if valor_inicial is not None and valor_inicial < 0:
            raise ValidationError({'valor_inicial': "O aporte inicial não pode ser um valor negativo."})

        if periodo_meses is not None and periodo_meses <= 0:
            raise ValidationError({'periodo_meses': "O período da simulação deve ser de pelo menos 1 mês."})