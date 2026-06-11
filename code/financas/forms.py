from django import forms

from usuarios.models import PerfilUsuario

from .models import Categoria, ContaBancaria, SimulacaoInvestimento, Transacao


def _aplica_bootstrap(form):
    """Aplica as classes do Bootstrap 5 aos widgets de um formulário."""
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
            widget.attrs.setdefault("class", "form-check-input")
        elif isinstance(widget, forms.Select):
            widget.attrs.setdefault("class", "form-select")
        else:
            widget.attrs.setdefault("class", "form-control")


class ContaBancariaForm(forms.ModelForm):
    """Formulário de conta bancária — o campo ``usuario`` não é exposto."""

    class Meta:
        model = ContaBancaria
        fields = ("nome", "saldo_atual")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplica_bootstrap(self)


class CategoriaForm(forms.ModelForm):
    """Formulário do catálogo de categorias (global)."""

    class Meta:
        model = Categoria
        fields = ("nome", "tipo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplica_bootstrap(self)


class TransacaoForm(forms.ModelForm):
    """Formulário de transação para o usuário final.

    Restringe o campo ``conta`` às contas do usuário logado e reaplica as
    validações de negócio (valor > 0; tipo da transação deve coincidir com o
    tipo da categoria) para que os erros apareçam por campo no template.
    """

    class Meta:
        model = Transacao
        fields = ("descricao", "valor", "data", "conta", "categoria", "tipo")
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        if usuario is not None:
            self.fields["conta"].queryset = ContaBancaria.objects.filter(usuario=usuario)
        _aplica_bootstrap(self)

    def clean(self):
        cleaned_data = super().clean()
        valor = cleaned_data.get("valor")
        tipo = cleaned_data.get("tipo")
        categoria = cleaned_data.get("categoria")

        if valor is not None and valor <= 0:
            self.add_error(
                "valor",
                "O valor de uma transação financeira deve ser estritamente maior que zero.",
            )

        if categoria and tipo and categoria.tipo != tipo:
            self.add_error(
                "categoria",
                f"Inconsistência detectada! A categoria '{categoria.nome}' está configurada "
                f"como {categoria.get_tipo_display()}, mas a transação foi marcada como "
                f"{dict(Transacao.TIPO_CHOICES).get(tipo)}. Os tipos devem coincidir.",
            )

        return cleaned_data


class SimulacaoInvestimentoForm(forms.ModelForm):
    """Formulário de simulação de investimento — o campo ``usuario`` não é exposto.

    Reaplica as validações de negócio do modelo (valores não-negativos;
    ``periodo_meses`` >= 1) para que os erros apareçam por campo no template.
    """

    class Meta:
        model = SimulacaoInvestimento
        fields = (
            "titulo",
            "valor_inicial",
            "aporte_mensal",
            "taxa_juros_anual",
            "periodo_meses",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplica_bootstrap(self)

    def clean(self):
        cleaned_data = super().clean()
        valor_inicial = cleaned_data.get("valor_inicial")
        aporte_mensal = cleaned_data.get("aporte_mensal")
        taxa_juros_anual = cleaned_data.get("taxa_juros_anual")
        periodo_meses = cleaned_data.get("periodo_meses")

        if valor_inicial is not None and valor_inicial < 0:
            self.add_error("valor_inicial", "O aporte inicial não pode ser um valor negativo.")

        if aporte_mensal is not None and aporte_mensal < 0:
            self.add_error("aporte_mensal", "O aporte mensal não pode ser um valor negativo.")

        if taxa_juros_anual is not None and taxa_juros_anual < 0:
            self.add_error("taxa_juros_anual", "A taxa de juros anual não pode ser negativa.")

        if periodo_meses is not None and periodo_meses <= 0:
            self.add_error("periodo_meses", "O período da simulação deve ser de pelo menos 1 mês.")

        return cleaned_data


class PerfilUsuarioForm(forms.ModelForm):
    """Edição do perfil financeiro (renda mensal e meta de patrimônio)."""

    class Meta:
        model = PerfilUsuario
        fields = ("renda_mensal", "meta_patrimonio")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _aplica_bootstrap(self)
