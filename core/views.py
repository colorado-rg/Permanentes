from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Listagem, ProcessoPermanente, ItemProcesso
from django.http import JsonResponse
import re


@login_required
def get_processos(request):
    caixa = request.GET.get('caixa')
    processos = ProcessoPermanente.objects.filter(caixa=caixa)
    
    # IMPORTANTE: Envia o número LIMPO para o frontend facilitar a comparação
    data = []
    for p in processos:
        data.append({
            'numero': apenas_numeros(p.numero), # Limpa aqui para bater com o leitor
            'numero_original': p.numero,        # Mantém o original para exibição se quiser
            'situacao': p.situacao if p.situacao else "Sem Situação"
        })
    
    return JsonResponse({'processos': data})    

# (Vamos precisar criar um formulário simples, mas por enquanto faremos sem)
@login_required
def home(request):
    # Página inicial que lista todas as listagens criadas pelo usuário
    listagens = Listagem.objects.filter(criador=request.user).order_by('-data_criacao')
    return render(request, 'core/home.html', {'listagens': listagens})

@login_required
def criar_listagem(request):
    # Busca todas as caixas para o autocomplete
    caixas_existentes = ProcessoPermanente.objects.exclude(caixa__isnull=True).exclude(caixa='').values_list('caixa', flat=True).distinct().order_by('caixa')

    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        
        # Pega a lista de TODOS os inputs com name="processos"
        lista_numeros = request.POST.getlist('processos') 
        
        # Validação do Título
        if not titulo:
            messages.error(request, 'O título é obrigatório.')
            return render(request, 'core/criar_listagem.html', {'caixas': caixas_existentes})

        # Validação/Criação
        try:
            # 1. Criar a Listagem
            listagem = Listagem.objects.create(titulo=titulo, criador=request.user)
            
            # 2. Processar cada número digitado
            itens_criados = 0
            for numero in lista_numeros:
                # Remove espaços e ignora campos vazios
                numero_limpo = numero.strip()
                if not numero_limpo:
                    continue
                
                # Verifica se é um número válido (opcional, mas recomendado)
                if not numero_limpo.isdigit() or len(numero_limpo) != 15:
                    messages.warning(request, f"O valor '{numero_limpo}' foi ignorado pois não parece um processo válido (15 dígitos).")
                    continue

                # Cria o item (a lógica de verificar se é permanente fica para depois ou podemos fazer agora)
                # Aqui vamos apenas criar o item na listagem.
                # A verificação se "e_permanente" fazemos na hora ou deixamos para a view de detalhe.
                # Para simplificar e ser rápido, vamos criar e marcar.
                
                eh_perm = ProcessoPermanente.objects.filter(numero=numero_limpo).exists()
                
                ItemProcesso.objects.create(
                    listagem=listagem,
                    numero_digitado=numero_limpo,
                    e_permanente=eh_perm
                )
                itens_criados += 1

            messages.success(request, f'Listagem "{titulo}" criada com {itens_criados} processos!')
            return redirect('detalhe_listagem', pk=listagem.pk)

        except Exception as e:
            messages.error(request, f'Erro ao salvar: {e}')
    
    return render(request, 'core/criar_listagem.html', {'caixas': caixas_existentes})

# Em core/views.py

@login_required
def conferir_caixa(request):
    """
    View específica para auditoria de caixas.
    """
    # Busca todas as caixas únicas para o autocomplete (ordenadas)
    caixas_existentes = ProcessoPermanente.objects.exclude(caixa__isnull=True).exclude(caixa='').values_list('caixa', flat=True).distinct().order_by('caixa')
    
    return render(request, 'core/conferir_caixa.html', {'caixas': caixas_existentes})


@login_required
def get_processos_caixa(request):
    """
    Retorna uma lista JSON de processos vinculados a uma caixa específica.
    Chamado via AJAX pelo javascript da página.
    """
    caixa_nome = request.GET.get('caixa', None)
    data = []

    if caixa_nome:
        # Filtra os processos daquela caixa e ordena pelo número
        processos = ProcessoPermanente.objects.filter(caixa=caixa_nome).order_by('numero')
        for proc in processos:
            data.append({
                'numero': proc.numero,
                'assunto': proc.assunto or 'Sem Assunto',
                'situacao': proc.situacao or '-'
            })
    
    return JsonResponse({'processos': data})

@login_required
def detalhe_listagem(request, pk):
    listagem = get_object_or_404(Listagem, pk=pk)

    if listagem.criador != request.user:
        messages.error(request, "Acesso não autorizado.")
        return redirect('home')

    if request.method == 'POST':
        
        # --- A CORREÇÃO ESTÁ AQUI ---
        # Verificamos se o botão 'submit_adicionar' foi o que enviou o formulário
        if 'submit_adicionar' in request.POST:
            
            # Agora podemos pegar o valor do input com segurança
            numero_digitado = request.POST.get('numero_processo')

            # Esta validação agora funcionará com o valor correto
            if not numero_digitado or not numero_digitado.isdigit() or len(numero_digitado) != 15:
                messages.error(request, "Número inválido. Deve ter 15 dígitos numéricos.")
                return redirect('detalhe_listagem', pk=listagem.pk)

            # --- A LÓGICA DE ALERTA (que já estava correta) ---
            try:
                # 1. Tenta encontrar o processo na base de dados permanente
                processo_perm = ProcessoPermanente.objects.get(numero=numero_digitado)
                
                # 2. SE ENCONTROU (PERMANENTE):
                messages.warning(request, f"O processo {numero_digitado} foi encontrado. Separe-o para registro em separado.")
                
                # 3. Registra na tabela Permanentes
                processo_perm.encontrado_por = request.user
                processo_perm.data_encontrado = timezone.now()
                processo_perm.listagem_encontrado = listagem
                processo_perm.save()
                
            except ProcessoPermanente.DoesNotExist:
                # 5. SE NÃO ENCONTROU (NORMAL):
                if ItemProcesso.objects.filter(listagem=listagem, numero_digitado=numero_digitado).exists():
                    messages.info(request, "Este processo já foi adicionado a esta listagem.")
                else:
                    ItemProcesso.objects.create(
                        listagem=listagem,
                        numero_digitado=numero_digitado,
                        e_permanente=False
                    )
            except Exception as e:
                messages.error(request, f"Ocorreu um erro inesperado: {e}")

            # Redireciona de volta para a listagem
            return redirect('detalhe_listagem', pk=listagem.pk)

    # Se for GET (ou um POST do botão 'apagar' que vai para outra view)
    itens = listagem.itens.all().order_by('data_adicionado')
    return render(request, 'core/detalhe_listagem.html', {'listagem': listagem, 'itens': itens})


@login_required
def editar_listagem(request, pk):
    """
    Esta view controla a edição do título de uma listagem existente.
    """
    
    listagem = get_object_or_404(Listagem, pk=pk)

    if listagem.criador != request.user:
        messages.error(request, "Acesso não autorizado.")
        return redirect('home')

    if request.method == 'POST':
        novo_titulo = request.POST.get('titulo')
        
        if novo_titulo:
            partes = novo_titulo.split('/')
            if len(partes) == 3 and len(partes[0]) == 4 and partes[0].isdigit() and len(partes[2]) == 2 and partes[2].isdigit():
                listagem.titulo = novo_titulo
                listagem.save()
                messages.success(request, 'Título da listagem atualizado com sucesso!')
                return redirect('detalhe_listagem', pk=listagem.pk)
            else:
                messages.error(request, 'Formato do título inválido. Use NNNN/TT/AA.')
        
    context = {
        'listagem': listagem
    }
    
    # --- A CORREÇÃO ESTÁ AQUI ---
    # O caminho deve ser relativo à pasta 'templates' do app
    return render(request, 'core/editar_listagem.html', context)


@login_required
def imprimir_listagem(request, pk):
    listagem = get_object_or_404(Listagem, pk=pk)
    if listagem.criador != request.user:
        messages.error(request, "Acesso não autorizado.")
        return redirect('home')
        
    itens = listagem.itens.all().order_by('data_adicionado')
    return render(request, 'core/imprimir_listagem.html', {'listagem': listagem, 'itens': itens})

# core/views.py (no final)

class RegisterView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('home') # Redireciona para a 'home' após o cadastro
    template_name = 'registration/register.html'

    # Esta função é chamada quando o formulário é válido
    # Vamos usá-la para logar o usuário automaticamente após o cadastro
    def form_valid(self, form):
        # Salva o usuário no banco de dados
        self.object = form.save()
        # Loga o usuário
        login(self.request, self.object)
        # Redireciona para a success_url ('home')
        return HttpResponseRedirect(self.get_success_url())
    
@login_required
def apagar_item(request, item_pk): # <-- O nome do argumento 'item_pk' deve corresponder à URL
    item = get_object_or_404(ItemProcesso, pk=item_pk)
    listagem = item.listagem

    # Garante que apenas o criador possa apagar
    if listagem.criador != request.user:
        messages.error(request, "Acesso não autorizado.")
        return redirect('detalhe_listagem', pk=listagem.pk)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'O processo foi removido da listagem.')
    
    return redirect('detalhe_listagem', pk=listagem.pk)

@login_required
def checar_processo_individual(request):
    """AJAX para conferência caixa a caixa"""
    numero_input = request.GET.get('numero', '').strip()
    
    # Usa a busca inteligente
    processo = buscar_processo_no_banco(numero_input)
    
    if processo:
        # Pega a situação exata
        situacao_db = processo.situacao
        situacao_texto = str(situacao_db).strip() if situacao_db else "Campo Nulo"
        if not situacao_texto: situacao_texto = "Vazio"

        # Verifica se é Permanente
        is_permanente = 'PERMANENTE' in situacao_texto.upper()
        
        return JsonResponse({
            'encontrado': True,
            'caixa_origem': processo.caixa,
            'situacao': situacao_texto,
            'is_permanente': is_permanente,
            'numero_db': processo.numero # Retorna o número oficial (15 dígitos) para exibir
        })
    else:
        return JsonResponse({'encontrado': False})

@login_required
def verificar_lote(request):
    """Verificação em massa (Cola Lista)"""
    context = {} 
    if request.method == 'POST':
        texto_colado = request.POST.get('lista_processos', '')
        context['texto_original'] = texto_colado
        
        # Regex captura sequências de 10 a 25 dígitos
        numeros_extraidos = re.findall(r'\d{10,25}', texto_colado)
        numeros_unicos = list(dict.fromkeys(numeros_extraidos))
        
        lista_permanentes = []
        lista_outros = []
        encontrados_map = {} # Evita duplicar objetos se inputs diferentes levarem ao mesmo processo

        for num_input in numeros_unicos:
            proc = buscar_processo_no_banco(num_input)
            
            if proc:
                # Usa o ID do processo como chave única
                if proc.id not in encontrados_map:
                    encontrados_map[proc.id] = True
                    
                    situacao = str(proc.situacao).upper() if proc.situacao else ""
                    if 'PERMANENTE' in situacao:
                        lista_permanentes.append(proc)
                    else:
                        lista_outros.append(proc)
        
        # Calcula não encontrados (baseado nos inputs originais)
        # Se o input achou alguém, conta como encontrado.
        # (Lógica simplificada: se total inputs > total achados, mostra diferença)
        # Para precisão total, teríamos que mapear input -> sucesso.
        
        # Aqui, vamos listar como "Não Encontrados" aqueles inputs que retornaram None
        nao_encontrados = []
        for num_input in numeros_unicos:
            if not buscar_processo_no_banco(num_input):
                nao_encontrados.append(num_input)

        context['sucesso'] = True
        context['qtd_verificados'] = len(numeros_unicos)
        context['qtd_encontrados'] = len(lista_permanentes) + len(lista_outros)
        context['lista_permanentes'] = lista_permanentes
        context['lista_outros'] = lista_outros
        context['nao_encontrados'] = nao_encontrados

    return render(request, 'core/verificar_lote.html', context)


def apenas_numeros(texto):
    """Remove tudo que não for dígito."""
    return re.sub(r'\D', '', str(texto)) if texto else ''

def buscar_processo_no_banco(numero_input):
    """
    Busca inteligente que lida com 10 dígitos (formato antigo) e 15/20 dígitos (novo).
    Prioriza encontrar registros PERMANENTES.
    """
    numero_limpo = apenas_numeros(numero_input)
    if not numero_limpo:
        return None

    # TENTATIVA 1: Busca Exata (Ideal)
    # Tenta pelo input original e pelo limpo
    for n in [numero_input, numero_limpo]:
        processo = ProcessoPermanente.objects.filter(numero=n).first()
        if processo: return processo

    # TENTATIVA 2: Busca por Conversão de 10 dígitos
    # Exemplo: Input 9919056901 (10 dígitos) -> Alvo 199971100056908
    if len(numero_limpo) == 10:
        # 1. Ignora o último dígito (Verificador antigo)
        corpo = numero_limpo[:-1] # Ex: 991905690
        
        # 2. Extrai o Ano (2 primeiros dígitos)
        ano_prefixo = corpo[:2] # 99
        try:
            if int(ano_prefixo) > 50: # Corte para 19xx vs 20xx
                ano_completo = '19' + ano_prefixo
            else:
                ano_completo = '20' + ano_prefixo
        except:
            ano_completo = '20' + ano_prefixo

        # 3. Extrai a Sequência Numérica (O "DNA" do processo)
        # Pegamos os últimos 5 dígitos do corpo. Isso ignora códigos de vara no meio.
        # Ex: De '991905690' pegamos '05690'.
        # O alvo '199971100056908' contem '05690'.
        sequencia_dna = corpo[-5:] 
        
        # Busca no banco: Começa com o Ano E contém a Sequência
        candidatos = ProcessoPermanente.objects.filter(
            numero__startswith=ano_completo,
            numero__contains=sequencia_dna
        )

        # 4. PRIORIDADE: Se achou mais de um, pega o que for PERMANENTE
        melhor_candidato = None
        for cand in candidatos:
            situacao = str(cand.situacao).upper() if cand.situacao else ""
            if 'PERMANENTE' in situacao:
                return cand # Achou um permanente! Retorna na hora.
            
            # Se não for permanente, guarda o primeiro que achou como "plano B"
            if not melhor_candidato:
                melhor_candidato = cand
        
        return melhor_candidato

    return None