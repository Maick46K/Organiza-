# 🗂️ Organiza+ — planner escolar (clone)

Clone funcional do app **Organiza+** (planejador do estudante), feito em **Django 4.2 + MySQL/MariaDB + Bootstrap 5**, rodando no pip5 na porta **8022**.

> Interface reproduzida a partir do app original (mesmas telas: **Painel**, **Calendário Anual** e **Configurações**), com as mesmas fontes (**Sora** + **Manrope**) e a paleta teal.

## Telas

| Tela | O que tem |
|---|---|
| **Painel** | **Tarefas** (título, matéria, entrega, prioridade alta/média/baixa — criar/editar/concluir/excluir), **Cronograma Hoje** (aulas do dia da semana) e **Informações escolares** (escola, turma, período) |
| **Calendário Anual** | 12 meses do ano, navegação de ano e edição por dia (título, descrição, dia letivo) |
| **Configurações** | Dados da escola/turma/período, tema escuro/claro e conta (sair) |
| **Usuários** | *(só administrador)* lista, **criar**, **editar** (permissões e senha) e **excluir** usuários — tabela `auth_user` |

No topo, à direita: **usuário logado** (com selo `admin`) e o botão **Sair da conta**.

## Alterações recentes

### 30/Set/2026 — CRUD de usuários, Cronograma só-admin, usuário logado e brasão

**CRUD de usuários** (`painel/views.py` + `painel/urls.py` + `templates/painel/usuarios.html`). O criar já existia; entraram **editar** (nome, e-mail, senha e permissões) e **excluir**, com proteções no servidor:

```python
# painel/views.py
@user_passes_test(_so_superusuario)
@require_POST
def usuario_editar(request, pk):
    alvo = get_object_or_404(User, pk=pk)
    eu = (alvo.pk == request.user.pk)
    if eu and not novo_super:
        messages.error(request, 'Você não pode remover o seu próprio acesso de administrador.')
        return redirect('usuarios')
    if alvo.is_superuser and not novo_super and User.objects.filter(is_superuser=True).count() <= 1:
        messages.error(request, 'Precisa haver pelo menos um administrador ativo.')
        return redirect('usuarios')
    ...  # first_name, last_name, email, is_superuser, is_staff, is_active
    if nova_senha:
        alvo.set_password(nova_senha)
```

```python
# painel/urls.py
path('usuarios/', views.usuarios, name='usuarios'),
path('usuarios/<int:pk>/editar/', views.usuario_editar, name='usuario_editar'),
path('usuarios/<int:pk>/excluir/', views.usuario_excluir, name='usuario_excluir'),
```

**Cronograma Hoje: só o administrador altera** — a trava é dupla (tela **e** servidor), então não adianta mandar o POST na mão.

```django
{# templates/painel/painel.html #}
{% if request.user.is_superuser %}
  <button class="btn-o" onclick="novaAula()">+</button>
{% else %}
  <span class="somente-leitura">somente leitura</span>
{% endif %}
```

```python
# painel/views.py
def aula_salvar(request):
    if not request.user.is_superuser:
        messages.error(request, 'Somente o administrador pode alterar o Cronograma Hoje.')
        return redirect('painel')
```

**Usuário logado no topo (à direita) e botão Sair** (`templates/painel/base.html`) — o sair é **POST** (com CSRF), que é o jeito correto no Django:

```django
<span class="usuario-logado">
  <span class="avatar">{{ request.user.username|first|upper }}</span>
  {{ request.user.get_full_name|default:request.user.username }}
  {% if request.user.is_superuser %}<span class="papel">admin</span>{% endif %}
</span>
<form method="post" action="{% url 'logout' %}">{% csrf_token %}
  <button class="btn-sair" type="submit">Sair da conta</button>
</form>
```

**Brasão da escola** — `static/painel/logo-santa.jpg` (redimensionado para 320 px), na barra lateral e na tela de login.

### 29/Set/2026 — tema escuro, contraste, cache e "sair"

**Tema escuro de verdade (e como padrão).** Antes o `:root` era claro e a classe `tema-claro` **não tinha nenhuma regra** no CSS — ligar o interruptor não mudava nada. Agora o escuro é o padrão e o claro vem da classe:

```css
/* static/painel/organiza.css */
:root {                      /* TEMA ESCURO (padrão) */
  color-scheme: dark;
  --fg: oklch(0.94 0.01 250);   --bg: oklch(0.19 0.02 260);
  --card: oklch(0.24 0.02 260); --campo: oklch(0.28 0.02 260);
}
body.tema-claro {             /* TEMA CLARO (interruptor ligado) */
  color-scheme: light;
  --fg: oklch(0.129 0.042 264.695); --bg: oklch(0.985 0.005 250);
  --card: #ffffff;                  --campo: #ffffff;
}
```

E o `background` fixo dos campos/modais (que deixava a letra "desbotada") virou variável de tema:

```css
/* antes */  .form-campo input { background: #fff; }
/* agora */  .form-campo input { background: var(--campo); color: var(--fg); }
```

**Bug de raiz: salvar a escola apagava o tema.** Cada formulário ganhou um marcador próprio:

```python
# painel/views.py
qual = request.POST.get('form')
if qual == 'escola':
    cfg.escola = ...; cfg.turma = ...; cfg.periodo = ...
elif qual == 'aparencia':
    cfg.tema_claro = request.POST.get('tema_claro') == 'on'
```

**Cache do CSS** (era o que mantinha o visual antigo na tela) — o link passou a levar versão:

```django
<link rel="stylesheet" href="{% static 'painel/organiza.css' %}?v=20260930b">
```

**Páginas sem cache + "sair" robusto** — `painel/middleware.py` (novo), registrado em `MIDDLEWARE`:

```python
class SemCache:
    def __call__(self, request):
        resposta = self.get_response(request)
        if not request.path.startswith('/static/'):
            resposta['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resposta
```

## Stack

- **Django 4.2** (LTS) + **MySQL/MariaDB** (`organiza` DB)
- **Bootstrap 5** + CSS próprio (`static/painel/organiza.css`) com a paleta do original
- Fontes Google: **Sora** (títulos) e **Manrope** (texto)
- Login com `django.contrib.auth` (usuário `admin`)

## Rodando

```bash
cd /home/pi/python/organiza
./venv/bin/python manage.py migrate
./venv/bin/python scripts/seed.py        # dados de exemplo + usuário admin (senha -> Cofre)
./venv/bin/python manage.py runserver 0.0.0.0:8022 --noreload
```

Em produção roda como **serviço systemd**: `organiza.service` (porta 8022), com o `.env` carregado por `EnvironmentFile`.

## Configuração (`.env`, não versionado)

```
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=0
DB_NAME=organiza
DB_USER=organiza
DB_PASSWORD=...      # no Cofre (entrada "organiza mysql")
DB_HOST=127.0.0.1
DB_PORT=3306
```

A senha do usuário web (`admin`) fica no **Cofre** (entrada `organiza web`).

## Estrutura

```
organiza/
├── organiza_project/     # settings/urls do projeto Django
├── painel/               # app: models, views, urls, contexto
├── templates/painel/     # base, painel, calendario, configuracoes, login
├── static/painel/        # organiza.css (paleta/fontes do original)
└── scripts/seed.py       # dados de exemplo + usuário admin
```

## Pendências / próximos passos

- [x] Autenticação multiusuário — CRUD de usuários na tela **Usuários** (só admin) — 30/Set/2026
- [x] Aulas por dia da semana editáveis pela interface — **Cronograma Hoje** (só admin altera) — 30/Set/2026
- [x] Tema escuro/claro funcionando (escuro é o padrão) — 29/Set/2026
- [ ] Revisar fidelidade visual lado a lado com o original
- [ ] Trocar senha pelo próprio usuário (aba "Minha conta")
- [ ] Notas por matéria (média e situação)
- [ ] Faltas/frequência por matéria
- [ ] PWA + lembrete de prazos
- [ ] Exportar/importar dados (JSON/CSV)

Maick46k
