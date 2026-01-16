import csv
import re
import os
from django.core.management.base import BaseCommand
from core.models import ProcessoPermanente

class Command(BaseCommand):
    help = 'Importa processos do arquivo dados.csv'

    def add_arguments(self, parser):
        parser.add_argument('arquivo_csv', type=str, help='Caminho do arquivo CSV')

    def handle(self, *args, **options):
        caminho = options['arquivo_csv']

        if not os.path.exists(caminho):
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {caminho}'))
            return

        self.stdout.write(self.style.WARNING('ATENÇÃO: Isso apagará o banco de dados atual para importar o novo.'))
        # Se quiser pular a confirmação para testes rápidos, comente as 3 linhas abaixo
        confirm = input("Deseja continuar? (s/n): ")
        if confirm.lower() != 's':
            self.stdout.write(self.style.ERROR('Cancelado.'))
            return

        # 1. Limpa o banco
        ProcessoPermanente.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Banco limpo. Iniciando leitura...'))

        objetos = []
        
        # 2. Lê o arquivo
        # Usamos 'utf-8' pois o arquivo é utf-8 (mesmo que tenha caracteres corrompidos gravados nele)
        with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
            # O arquivo usa VÍRGULA como separador
            reader = csv.DictReader(f, delimiter=',')
            
            for row in reader:
                # Mapeamento: Nome na Planilha -> Nome no Banco
                
                # Processo -> numero
                raw_num = row.get('Processo', '')
                num_limpo = re.sub(r'\D', '', raw_num) # Remove pontos e traços

                if not num_limpo:
                    continue

                # Cria o objeto na memória
                obj = ProcessoPermanente(
                    numero=num_limpo,
                    caixa=row.get('Caixa', '').strip(),     # Coluna 'Caixa'
                    situacao=row.get('Situacao', '').strip(), # Coluna 'Situacao'
                    assunto=row.get('Assunto', '').strip(),   # Coluna 'Assunto'
                    # Se seu modelo tiver o campo 'classe', descomente a linha abaixo:
                    # classe=row.get('Classe', '').strip(),
                )
                objetos.append(obj)

        # 3. Salva no Banco (Bulk Create para ser rápido)
        ProcessoPermanente.objects.bulk_create(objetos)
        
        self.stdout.write(self.style.SUCCESS(f'SUCESSO! {len(objetos)} processos importados.'))