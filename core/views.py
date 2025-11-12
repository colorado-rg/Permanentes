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
import re

# (Vamos precisar criar um formulário simples, mas por enquanto faremos sem)
@login_required
def home(request):
    # Página inicial que lista todas as listagens criadas pelo usuário
    listagens = Listagem.objects.filter(criador=request.user).order_by('-data_criacao')
    return render(request, 'core/home.html', {'listagens': listagens})

@login_required
def criar_listagem(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        if titulo:
            # Validação simples do formato NNNN/TT/AA (pode ser melhorada)
            partes = titulo.split('/')
            if len(partes) == 3 and len(partes[0]) == 4 and partes[0].isdigit() and len(partes[2]) == 2 and partes[2].isdigit():
                listagem = Listagem.objects.create(titulo=titulo, criador=request.user)
                return redirect('detalhe_listagem', pk=listagem.pk)
            else:
                messages.error(request, 'Formato do título inválido. Use NNNN/TT/AA.')
        
    return render(request, 'core/criar_listagem.html')


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
def verificar_lote(request):
    """
    Controla a página de verificação em lote.
    Recebe um texto, extrai números de 15 dígitos e 
    verifica quais deles são Permanentes.
    """
    context = {} # Contexto para enviar dados para o template

    if request.method == 'POST':
        # 1. Obter o texto colado
        texto_colado = request.POST.get('lista_processos', '')
        context['texto_original'] = texto_colado # Devolve o texto para a textarea
        
        # 2. Extrair todos os números de 15 dígitos do texto
        # \b = fronteira da palavra (impede apanhar números dentro de outros)
        # \d{15} = exatamente 15 dígitos
        numeros_extraidos = re.findall(r'\b\d{15}\b', texto_colado)
        
        if not numeros_extraidos:
            messages.error(request, 'Nenhum número de processo (15 dígitos) válido foi encontrado no texto.')
            return render(request, 'core/verificar_lote.html', context)

        # 3. Consultar o banco de dados de forma eficiente
        # Usamos __in para verificar todos os números numa única consulta
        # values_list('numero', flat=True) devolve uma lista simples [num1, num2]
        permanentes_encontrados = ProcessoPermanente.objects.filter(
            numero__in=numeros_extraidos
        ).values_list('numero', flat=True)
        
        # 4. Enviar os resultados de volta para o template
        context['resultados_encontrados'] = list(permanentes_encontrados)
        context['total_verificados'] = len(numeros_extraidos)

    # Se for GET, ou depois do POST, renderiza a página
    return render(request, 'core/verificar_lote.html', context)