from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin, TabularInline
from .models import ContaBancaria, Categoria, Transacao, SimulacaoInvestimento


class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        valor = cleaned_data.get('valor')
        tipo = cleaned_data.get('tipo')
        categoria = cleaned_data.get('categoria')

        if valor is not None and valor <= 0:
            self.add_error('valor', "O valor de uma transação financeira deve ser estritamente maior que zero.")

        if categoria and tipo:
            if categoria.tipo != tipo:
                self.add_error(
                    'categoria',
                    f"Inconsistência detectada! A categoria '{categoria.nome}' está configurada no sistema "
                    f"como {categoria.get_tipo_display()}, mas a transação foi marcada como {dict(Transacao.TIPO_CHOICES).get(tipo)}. "
                    f"Os tipos devem coincidir."
                )

        return cleaned_data


class SimulacaoInvestimentoForm(forms.ModelForm):
    class Meta:
        model = SimulacaoInvestimento
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        valor_inicial = cleaned_data.get('valor_inicial')
        aporte_mensal = cleaned_data.get('aporte_mensal')
        taxa_juros_anual = cleaned_data.get('taxa_juros_anual')
        periodo_meses = cleaned_data.get('periodo_meses')

        if valor_inicial is not None and valor_inicial < 0:
            self.add_error('valor_inicial', "O aporte inicial não pode ser um valor negativo.")

        if aporte_mensal is not None and aporte_mensal < 0:
            self.add_error('aporte_mensal', "O aporte mensal não pode ser um valor negativo.")

        if taxa_juros_anual is not None and taxa_juros_anual < 0:
            self.add_error('taxa_juros_anual', "A taxa de juros anual não pode ser negativa.")

        if periodo_meses is not None and periodo_meses <= 0:
            self.add_error('periodo_meses', "O período da simulação deve ser de pelo menos 1 mês.")

        return cleaned_data


class TransacaoInline(TabularInline):
    model = Transacao
    form = TransacaoForm
    extra = 1
    fields = ('data', 'descricao', 'tipo', 'categoria', 'valor')


@admin.register(ContaBancaria)
class ContaBancariaAdmin(ModelAdmin):
    list_display = ('nome', 'usuario', 'saldo_atual')
    list_filter = ('usuario',)
    search_fields = ('nome', 'usuario__username')
    inlines = [TransacaoInline]

    def save_model(self, request, obj, form, change):
        if not change and not obj.usuario_id:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

    def get_exclude(self, request, obj=None):
        if not request.user.is_superuser:
            return ('usuario',)
        return super().get_exclude(request, obj)


@admin.register(Categoria)
class CategoriaAdmin(ModelAdmin):
    list_display = ('nome', 'tipo')
    list_filter = ('tipo',)
    search_fields = ('nome',)


@admin.register(Transacao)
class TransacaoAdmin(ModelAdmin):
    form = TransacaoForm
    list_display = ('data', 'descricao', 'conta', 'categoria', 'tipo', 'valor')
    list_filter = ('tipo', 'conta', 'categoria', 'data')
    search_fields = ('descricao',)


@admin.register(SimulacaoInvestimento)
class SimulacaoInvestimentoAdmin(ModelAdmin):
    form = SimulacaoInvestimentoForm
    list_display = ('titulo', 'usuario', 'valor_inicial', 'aporte_mensal', 'taxa_juros_anual', 'periodo_meses', 'data_criacao')
    list_filter = ('data_criacao', 'periodo_meses', 'usuario')
    search_fields = ('titulo', 'usuario__username')

    def save_model(self, request, obj, form, change):
        if not change and not obj.usuario_id:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

    def get_exclude(self, request, obj=None):
        if not request.user.is_superuser:
            return ('usuario',)
        return super().get_exclude(request, obj)