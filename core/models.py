from django.db import models
from django.contrib.auth.models import User

class ProcessoPermanente(models.Model):
    """
    Tabela principal que conterá todos os dados importados do Excel.
    """
    # --- DADOS DO PROCESSO (Vindos da Tabela) ---
    numero = models.CharField(max_length=15, unique=True, help_text="Número de 15 dígitos do processo permanente.")
    
    classe = models.CharField(max_length=255, verbose_name="Classe", blank=True, null=True)
    situacao = models.CharField(max_length=255, verbose_name="Situação", blank=True, null=True)
    assunto = models.CharField(max_length=255, verbose_name="Assunto", blank=True, null=True)
    orgao_atual = models.CharField(max_length=255, verbose_name="Órgão Atual", blank=True, null=True)
    localizador = models.CharField(max_length=255, verbose_name="Localizador", blank=True, null=True)
    
    # A segunda coluna 'SITUAÇÃO' da tabela original renomeada
    situacao_detalhe = models.CharField(max_length=255, verbose_name="Situação Detalhe", blank=True, null=True)
    
    caixa = models.CharField(max_length=50, verbose_name="Caixa", blank=True, null=True)

    # --- LÓGICA DE CONTROLE (Encontrado por quem?) ---
    encontrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="processos_encontrados")
    data_encontrado = models.DateTimeField(null=True, blank=True)
    listagem_encontrado = models.ForeignKey('Listagem', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.numero} - {self.caixa or 'Sem Caixa'}"

class Listagem(models.Model):
    # Título no formato NNNN/TT/AA
    titulo = models.CharField(max_length=100, help_text="Formato: NNNN/TT/AA")
    criador = models.ForeignKey(User, on_delete=models.PROTECT)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} (Criada por: {self.criador.username})"

class ItemProcesso(models.Model):
    # O processo que o usuário digitou na listagem
    numero_digitado = models.CharField(max_length=15)
    listagem = models.ForeignKey(Listagem, on_delete=models.CASCADE, related_name="itens")
    
    # Marca se este item foi encontrado na base permanente
    e_permanente = models.BooleanField(default=False)
    data_adicionado = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Garante que o mesmo número não seja digitado duas vezes na MESMA lista
        unique_together = ('listagem', 'numero_digitado') 

    def __str__(self):
        return f"{self.numero_digitado} (Lista: {self.listagem.titulo})"