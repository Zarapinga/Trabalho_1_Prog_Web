from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class RegistroForm(UserCreationForm):
    """Formulário de cadastro do usuário final.

    Estende o UserCreationForm nativo, adicionando o e-mail (opcional) ao
    cadastro. A senha e suas validações continuam sendo as do Django.
    """

    email = forms.EmailField(
        label="E-mail",
        required=False,
        help_text="Opcional. Usado para contato e recuperação de conta.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplica a classe do Bootstrap 5 a todos os campos do formulário.
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class LoginForm(AuthenticationForm):
    """AuthenticationForm com as classes do Bootstrap 5 aplicadas aos campos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
