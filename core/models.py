from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ProcessoPermanente(models.Model):
    # O processo de 15 dígitos
    numero = models.CharField(max_length=15, unique=True, help_text="Número de 15 dígitos do processo permanente.")
    
    # Campos que serão preenchidos quando for encontrado
    encontrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="processos_encontrados")
    data_encontrado = models.DateTimeField(null=True, blank=True)
    listagem_encontrado = models.ForeignKey('Listagem', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.numero

class Listagem(models.Model):
    # Título no formato NNNN/TT/AA
    titulo = models.CharField(max_length=100, help_text="Formato: NNNN/TT/AA")
    criador = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} (Criada por: {self.criador.username})"

class ItemProcesso(models.Model):
    # O processo que o usuário digitou
    numero_digitado = models.CharField(max_length=15)
    # A listagem à qual este item pertence
    listagem = models.ForeignKey(Listagem, on_delete=models.CASCADE, related_name="itens")
    # Um campo para marcar se este item foi encontrado na base permanente
    e_permanente = models.BooleanField(default=False)
    data_adicionado = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Garante que o mesmo número não seja digitado duas vezes na MESMA lista
        unique_together = ('listagem', 'numero_digitado') 

    def __str__(self):
        return f"{self.numero_digitado} (Lista: {self.listagem.titulo})"