from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuário")
    renda_mensal = models.DecimalField("Renda Mensal (R$)", max_digits=12, decimal_places=2, default=0.00, help_text="Sua receita média mensal fixa")
    meta_patrimonio = models.DecimalField("Meta de Patrimônio (R$)", max_digits=12, decimal_places=2, default=0.00, help_text="Quanto você deseja acumular no total")
    data_atualizacao = models.DateTimeField("Última Atualização", auto_now=True)

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"

    def __str__(self):
        return f"Perfil de {self.user.username}"