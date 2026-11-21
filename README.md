<!-- template:start -->
# template-workspace

Template do repositório `workspace` de uma organização: CLI de orquestração (pacote
[`kcm-workspace`](https://github.com/python-by-kelsoncm/python-kcm-workspace)), `docker compose` de desenvolvimento,
workspace multi-root do VS Code e `plano.md`.

## Como usar

1. **Use this template > Create a new repository**, normalmente `<org>/workspace`, **privado**.
2. Clone e rode o inicializador (só biblioteca padrão do Python 3.10+):

   ```bash
   python template_init.py --cli mfs --title "Minha Suite" --stack moodle
   ```

   - `--cli`: nome curto da CLI (padrão: iniciais da organização + `w`, ex.: `django-by-kelsoncm` → `dbkw`).
   - `--stack`: `moodle` (Moodle 5.3 + PostgreSQL), `django` (Django + PostgreSQL) ou `none`.

   Ele renomeia `__cli__`, `__cli__.ps1` e `__cli__.code-workspace`, troca os marcadores, cria o
   `docker-compose.yml` e se apaga. Use `--dry-run` para conferir antes.
3. `cp .env.example .env` e troque as senhas. O `.env` não vai para o git.

---
<!-- template:end -->
# {{TITLE}}: workspace

> **_APENAS PARA DESENVOLVIMENTO_**, **NÃO suba em produção**.

Orquestração e desenvolvimento local da organização [`{{OWNER}}`](https://github.com/{{OWNER}}):
`docker compose`, o script `__cli__` e o workspace multi-root do VS Code.

## Estrutura de pastas

```text
<pasta da organização>/
   ├── workspace    # Este repositório (CLI, Docker Compose, VS Code Workspace)
   ├── pages        # Portal {{OWNER}}.github.io
   └── profile      # Perfil e arquivos comunitários (.github)
```

## Desenvolva

Pré-requisitos: Git, Docker com Docker Compose, [uv](https://docs.astral.sh/uv/) e chave SSH no GitHub com acesso à
organização.

```bash
git clone git@github.com:{{OWNER}}/workspace.git workspace
cd workspace
cp .env.example .env   # troque as senhas
./__cli__ setup
```

O `__cli__ setup` clona os repositórios listados no script ao lado deste workspace. Depois:

```bash
code __cli__.code-workspace
./__cli__ launch
```

| Comando | Descrição |
| :--- | :--- |
| `__cli__ setup` | Clona todos os repositórios e prepara o ambiente local |
| `__cli__ launch` | Inicia os serviços Docker e acompanha os logs |
| `__cli__ relaunch` | Reinicia os containers em background |
| `__cli__ shell <serviço>` | Abre um shell dentro do container |
| `__cli__ git <comando>` | Executa o comando git em todos os repositórios (ex.: `__cli__ git status`) |
| `__cli__ <comando>` | Qualquer outro comando é repassado ao `docker compose` |

No Windows, use `__cli__.ps1`.

## Segredos

Credenciais ficam só no `.env` (ignorado pelo git). O `.env.example` traz os nomes das variáveis com valores de
exemplo que devem ser trocados.
