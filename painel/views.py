import calendar as pycalendar
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Aula, ConfiguracaoEscola, EventoCalendario, Tarefa

MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


def _hoje():
    return datetime.date.today()


@login_required
def painel(request):
    tarefas = Tarefa.objects.all()
    dia_semana = _hoje().weekday()
    aulas = Aula.objects.filter(dia_semana=dia_semana)
    return render(request, 'painel/painel.html', {
        'tarefas': tarefas,
        'aulas': aulas,
        'hoje': _hoje(),
        'prioridades': Tarefa.PRIORIDADES,
        'dias': Aula.DIAS,
        'menu': 'painel',
    })


@login_required
@require_POST
def tarefa_salvar(request):
    t_id = request.POST.get('id')
    titulo = (request.POST.get('titulo') or '').strip()
    materia = (request.POST.get('materia') or '').strip()
    entrega = request.POST.get('entrega') or _hoje().isoformat()
    prioridade = request.POST.get('prioridade') or 'media'
    if not titulo:
        messages.error(request, 'Informe o título da tarefa.')
        return redirect('painel')
    if t_id:
        t = get_object_or_404(Tarefa, pk=t_id)
        t.titulo, t.materia, t.prioridade = titulo, materia, prioridade
        t.entrega = entrega
        t.save()
        messages.success(request, 'Tarefa atualizada.')
    else:
        Tarefa.objects.create(titulo=titulo, materia=materia, entrega=entrega, prioridade=prioridade)
        messages.success(request, 'Tarefa criada.')
    return redirect('painel')


@login_required
@require_POST
def tarefa_excluir(request, pk):
    get_object_or_404(Tarefa, pk=pk).delete()
    messages.success(request, 'Tarefa excluída.')
    return redirect('painel')


@login_required
@require_POST
def tarefa_concluir(request, pk):
    t = get_object_or_404(Tarefa, pk=pk)
    t.concluida = not t.concluida
    t.save()
    return redirect('painel')


@login_required
@require_POST
def aula_salvar(request):
    a_id = request.POST.get('id')
    disciplina = (request.POST.get('disciplina') or '').strip()
    local = (request.POST.get('local') or '').strip()
    horario = request.POST.get('horario') or '07:00'
    dia = int(request.POST.get('dia_semana') or _hoje().weekday())
    if not disciplina:
        messages.error(request, 'Informe a disciplina.')
        return redirect('painel')
    if a_id:
        a = get_object_or_404(Aula, pk=a_id)
        a.disciplina, a.local, a.horario, a.dia_semana = disciplina, local, horario, dia
        a.save()
        messages.success(request, 'Aula atualizada.')
    else:
        Aula.objects.create(disciplina=disciplina, local=local, horario=horario, dia_semana=dia)
        messages.success(request, 'Aula adicionada.')
    return redirect('painel')


@login_required
@require_POST
def aula_excluir(request, pk):
    get_object_or_404(Aula, pk=pk).delete()
    messages.success(request, 'Aula removida.')
    return redirect('painel')


@login_required
def calendario(request):
    ano = int(request.GET.get('ano') or _hoje().year)
    eventos = {e.data: e for e in EventoCalendario.objects.filter(data__year=ano)}
    meses = []
    for mes in range(1, 13):
        cal = pycalendar.Calendar(firstweekday=6)  # domingo primeiro
        semanas = []
        for semana in cal.monthdatescalendar(ano, mes):
            linha = []
            for d in semana:
                linha.append({
                    'dia': d.day,
                    'fora': d.month != mes,
                    'data': d,
                    'evento': eventos.get(d),
                    'hoje': d == _hoje(),
                })
            semanas.append(linha)
        meses.append({'numero': mes, 'nome': MESES[mes - 1], 'semanas': semanas})
    return render(request, 'painel/calendario.html', {
        'meses': meses, 'ano': ano, 'ano_ant': ano - 1, 'ano_prox': ano + 1, 'menu': 'calendario',
    })


@login_required
@require_POST
def evento_salvar(request):
    data = request.POST.get('data')
    if not data:
        return JsonResponse({'ok': False, 'erro': 'sem data'}, status=400)
    ev, _criado = EventoCalendario.objects.get_or_create(data=data)
    ev.titulo = (request.POST.get('titulo') or '')[:120]
    ev.descricao = request.POST.get('descricao') or ''
    ev.letivo = request.POST.get('letivo') in ('1', 'true', 'on', 'True')
    ev.save()
    return JsonResponse({'ok': True, 'data': str(ev.data), 'titulo': ev.titulo})


@login_required
def configuracoes(request):
    cfg = ConfiguracaoEscola.atual()
    if request.method == 'POST':
        # Cada form manda seu proprio marcador ('form'): antes, salvar as informacoes
        # da escola (form sem o campo do tema) ZERAVA o tema escolhido.
        qual = request.POST.get('form')
        if qual == 'escola':
            cfg.escola = (request.POST.get('escola') or cfg.escola)[:120]
            cfg.turma = (request.POST.get('turma') or cfg.turma)[:80]
            cfg.periodo = (request.POST.get('periodo') or cfg.periodo)[:80]
        elif qual == 'aparencia':
            # a tela mostra "Tema claro": marcado = claro; desmarcado = escuro (padrao)
            cfg.tema_claro = request.POST.get('tema_claro') == 'on'
        cfg.save()
        messages.success(request, 'Configurações salvas.')
        return redirect('configuracoes')
    return render(request, 'painel/configuracoes.html', {'cfg': cfg, 'menu': 'configuracoes'})


def _so_superusuario(u):
    return u.is_authenticated and u.is_superuser


@user_passes_test(_so_superusuario)
def usuarios(request):
    """Lista e cria usuarios (tabela auth_user do Django). Só superusuario."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            novo = form.save()
            messages.success(request, 'Usuario "%s" criado.' % novo.username)
            return redirect('usuarios')
        partes = []
        for campo, erros in form.errors.items():
            partes.append('%s: %s' % (campo, ' '.join(erros)))
        messages.error(request, 'Nao foi possivel criar: ' + ' | '.join(partes))
    else:
        form = UserCreationForm()
    return render(request, 'painel/usuarios.html', {
        'form': form,
        'usuarios': User.objects.order_by('username'),
        'menu': 'usuarios',
    })
