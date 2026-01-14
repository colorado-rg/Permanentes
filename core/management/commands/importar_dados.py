import csv
import os
from django.core.management.base import BaseCommand
from core.models import ProcessoPermanente

class Command(BaseCommand):
    help = 'Importa dados do arquivo dados.csv para o banco de dados'

    def handle(self, *args, **kwargs):
        nome_arquivo = 'dados.csv'
        caminho = os.path.join(os.getcwd(), nome_arquivo)

        if not os.path.exists(caminho):
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {caminho}. Coloque-o na pasta raiz.'))
            return

        self.stdout.write(f'--- Iniciando importação de: {nome_arquivo} ---')

        # ALTERAÇÃO AQUI: Mudamos de 'utf-8-sig' para 'latin-1' para ler arquivos do Excel/Windows
        try:
            arquivo_csv = open(caminho, 'r', encoding='latin-1')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao abrir arquivo. Tente salvar o CSV como "CSV UTF-8". Erro: {e}'))
            return

        with arquivo_csv:
            # Lê a primeira linha para descobrir se o separador é , ou ;
            primeira_linha = arquivo_csv.readline()
            separador = ';' if ';' in primeira_linha else ','
            arquivo_csv.seek(0) # Volta para o início

            self.stdout.write(f'Separador detectado: "{separador}"')

            leitor = csv.DictReader(arquivo_csv, delimiter=separador)
            
            # Normalizar cabeçalhos: Maiúsculas e sem espaços nas pontas
            leitor.fieldnames = [name.strip().upper() for name in leitor.fieldnames]
            self.stdout.write(f'Colunas detectadas: {leitor.fieldnames}')

            contador_sucesso = 0
            contador_erro = 0
            
            for linha in leitor:
                try:
                    # Tenta pegar o processo. Se a coluna for "Processo", vira "PROCESSO"
                    numero_bruto = linha.get('PROCESSO')
                    
                    if not numero_bruto:
                        continue 

                    # Limpa o número (apenas dígitos)
                    numero_limpo = ''.join(filter(str.isdigit, numero_bruto))

                    if not numero_limpo:
                        continue

                    # Cria ou Atualiza
                    obj, created = ProcessoPermanente.objects.update_or_create(
                        numero=numero_limpo,
                        defaults={
                            'classe': linha.get('CLASSE', ''),
                            'situacao': linha.get('SITUAÇÃO', ''), 
                            'assunto': linha.get('ASSUNTO', ''),
                            'orgao_atual': linha.get('ÓRGÃO ATUAL', '') or linha.get('ORGAO ATUAL', ''),
                            'localizador': linha.get('LOCALIZADOR', ''),
                            
                            # Tenta variações do nome da coluna "Situação Detalhe"
                            'situacao_detalhe': (
                                linha.get('SITUAÇÃO_DETALHE') or 
                                linha.get('SITUACAO_DETALHE') or 
                                linha.get('SITUAÇÃO DETALHE') or
                                linha.get('SITUAÇÃO.1') # Às vezes o Excel faz isso com colunas duplicadas
                            ), 
                            
                            'caixa': linha.get('CAIXA', ''),
                        }
                    )
                    
                    contador_sucesso += 1
                    if contador_sucesso % 500 == 0:
                        self.stdout.write(f'... Processados {contador_sucesso} ...')

                except Exception as e:
                    contador_erro += 1
                    # Mostra o erro mas continua a importação
                    # self.stdout.write(self.style.WARNING(f'Erro na linha: {e}'))

        self.stdout.write(self.style.SUCCESS(f'--- Concluído! ---'))
        self.stdout.write(f'Sucesso: {contador_sucesso}')
        self.stdout.write(f'Erros: {contador_erro}')