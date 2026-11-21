#!/usr/bin/env python3
"""Inicializa um repositório gerado a partir do template-workspace.

Renomeia a CLI ``__cli__`` (ex.: ``mfs``), troca os marcadores ({{OWNER}}, {{TITLE}}...), escolhe o
``docker-compose.yml`` da stack (moodle, django ou nenhuma) e, por fim, apaga este script.

Uso (na raiz do repositório recém-criado, normalmente ``<org>/workspace``):

    python template_init.py                       # pergunta o que não conseguir deduzir
    python template_init.py --cli mfs --title "Moodle Fields Suite" --stack moodle --yes
    python template_init.py --dry-run             # mostra o que mudaria, sem alterar nada

Sem dependências externas: só a biblioteca padrão do Python 3.10+.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SELF = Path(__file__).resolve()
SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "__pycache__", "_build", "_site", "dist"}
TEMPLATE_BLOCK = re.compile(r"<!-- template:start -->.*?<!-- template:end -->\n*", re.S)
RST_UNDERLINE = re.compile(r"^([=\-~^\"'`#*+])\1+$")


def git(*args: str) -> str:
    """Executa um comando git na raiz e devolve a saída (vazia se o git falhar)."""
    try:
        result = subprocess.run(  # noqa: S603 - argumentos fixos, git do PATH do desenvolvedor
            ["git", *args],  # noqa: S607
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def remote_owner_repo() -> tuple[str, str]:
    """Deduz dono e nome do repositório pela URL do remoto ``origin``."""
    match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", git("remote", "get-url", "origin"))
    return (match.group(1), match.group(2)) if match else ("", "")


def ask(label: str, default: str, interactive: bool) -> str:
    """Pergunta um valor no terminal, usando o padrão quando não houver resposta."""
    if not interactive:
        return default
    answer = input(f"{label} [{default}]: ").strip() if default else input(f"{label}: ").strip()
    return answer or default


def iter_paths() -> list[Path]:
    """Lista arquivos e pastas do repositório, ignorando .git, dependências e saídas de build."""
    paths = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts) or path == SELF:
            continue
        paths.append(path)
    return paths


def fix_rst_underlines(text: str) -> str:
    """Ajusta o sublinhado dos títulos reStructuredText ao novo tamanho do título."""
    lines = text.split("\n")
    for i in range(1, len(lines)):
        title = lines[i - 1]
        if title.strip() and not RST_UNDERLINE.match(title) and RST_UNDERLINE.match(lines[i]):
            lines[i] = lines[i][0] * max(len(title), 3)
    return "\n".join(lines)


def apply(replacements: dict[str, str], dry_run: bool) -> None:
    """Troca os marcadores no conteúdo e nos nomes dos arquivos e pastas."""
    ordered = sorted(replacements.items(), key=lambda item: -len(item[0]))
    for path in iter_paths():
        if not path.is_file():
            continue
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue  # binário (imagens, fontes...)
        new = text
        for old, value in ordered:
            new = new.replace(old, value)
        new = TEMPLATE_BLOCK.sub("", new)
        if path.suffix == ".rst":
            new = fix_rst_underlines(new)
        if new != text:
            print(f"  editado:   {path.relative_to(ROOT).as_posix()}")
            if not dry_run:
                path.write_bytes(new.encode("utf-8"))
    for path in sorted(iter_paths(), key=lambda p: len(p.parts), reverse=True):
        name = path.name
        for old, value in ordered:
            name = name.replace(old, value)
        if name != path.name:
            print(f"  renomeado: {path.relative_to(ROOT).as_posix()} -> {name}")
            if not dry_run:
                path.rename(path.with_name(name))


def common_arguments(parser: argparse.ArgumentParser, owner: str) -> None:
    """Argumentos comuns a todos os templates."""
    parser.add_argument("--owner", default=owner, help="organização ou usuário do GitHub (padrão: remoto origin)")
    parser.add_argument("--author", default=git("config", "user.name"))
    parser.add_argument("--email", default=git("config", "user.email"))
    parser.add_argument("--yes", action="store_true", help="não pergunta nada; usa argumentos e padrões")
    parser.add_argument("--dry-run", action="store_true", help="só mostra o que mudaria")


def require(values: dict[str, str]) -> bool:
    """Confere se nenhum valor ficou vazio."""
    missing = [key for key, value in values.items() if not value]
    if missing:
        print(f"erro: informe {', '.join(missing)} (veja --help)", file=sys.stderr)
        return False
    return True


def finish(dry_run: bool, steps: list[str]) -> None:
    """Apaga este script e mostra os próximos passos."""
    if dry_run:
        return
    SELF.unlink()
    print("\nPronto. Próximos passos:")
    for number, step in enumerate(["Revise as mudanças com `git status` e `git diff`.", *steps], 1):
        print(f"  {number}. {step}")


CLI_RE = re.compile(r"^[a-z][a-z0-9]{1,15}$")
STACKS = ("moodle", "django", "none")


def main() -> int:
    import shutil

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    owner, _repo = remote_owner_repo()
    initials = "".join(part[0] for part in re.split(r"[-_]", owner) if part) + "w" if owner else ""

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cli", default=initials, help="nome curto da CLI, ex.: mfs (padrão: iniciais do dono + w)")
    parser.add_argument("--title", default="", help="nome legível da organização/família")
    parser.add_argument("--stack", choices=STACKS, default="moodle", help="docker compose inicial (padrão: moodle)")
    common_arguments(parser, owner)
    args = parser.parse_args()

    interactive = not args.yes and sys.stdin.isatty()
    cli = ask("Nome da CLI", args.cli, interactive)
    if not CLI_RE.match(cli):
        print(
            f"erro: CLI inválida {cli!r}: use de 2 a 16 letras minúsculas e números, começando por letra",
            file=sys.stderr,
        )
        return 2
    stack = ask(f"Stack ({'/'.join(STACKS)})", args.stack, interactive)
    if stack not in STACKS:
        print(f"erro: stack inválida {stack!r}; use {', '.join(STACKS)}", file=sys.stderr)
        return 2
    values = {
        "{{OWNER}}": ask("Dono no GitHub", args.owner, interactive),
        "{{TITLE}}": ask("Nome legível", args.title or args.owner, interactive),
        "{{AUTHOR}}": ask("Autor", args.author, interactive),
        "{{EMAIL}}": ask("E-mail do autor", args.email, interactive),
        "{{YEAR}}": str(date.today().year),
    }
    if not require(values):
        return 2
    values["__cli__"] = cli

    print(f"Inicializando o workspace {cli} (stack {stack}){' [dry-run]' if args.dry_run else ''}")
    compose_dir = ROOT / "compose"
    if not args.dry_run:
        if stack != "none":
            shutil.copyfile(compose_dir / f"{stack}.yml", ROOT / "docker-compose.yml")
        shutil.rmtree(compose_dir)
    print(f"  compose:   {'docker-compose.yml <- compose/' + stack + '.yml' if stack != 'none' else 'nenhum'}")
    apply(values, args.dry_run)
    if not args.dry_run:
        (ROOT / cli).chmod(0o755)
    finish(
        args.dry_run,
        [
            "Copie .env.example para .env e troque as senhas (o .env não vai para o git).",
            f"Liste os repositórios da organização em `{cli}` e em `{cli}.code-workspace`.",
            f"Rode `./{cli} setup` (ou `.\\{cli}.ps1 setup` no Windows) para clonar tudo ao lado do workspace.",
            "Faça o commit inicial.",
        ],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
