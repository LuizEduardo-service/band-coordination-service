#!/usr/bin/env python3
"""
Varre frontend/*.py em busca de padrões que costumam quebrar em Flet 0.21.
Uso (na raiz do repositório escala-louvor):
  python .cursor/skills/flet-frontend-validate/scripts/check_flet_patterns.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Raiz do repo: .../escala-louvor
ROOT = Path(__file__).resolve().parents[4]
FRONTEND = ROOT / "frontend"

RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "ft.Wrap ou Wrap(",
        re.compile(r"\bWrap\s*\("),
        "Em várias versões do Flet não existe Wrap; use ft.Row(..., wrap=True).",
    ),
    (
        "InkWell",
        re.compile(r"\bInkWell\s*\("),
        "Pode não existir no Flet do projeto; use GestureDetector + Tooltip.",
    ),
    (
        "foreground_image_src em CircleAvatar",
        re.compile(r"CircleAvatar\s*\([^)]*foreground_image_src"),
        "Em Flet 0.21 costuma ser foreground_image_url; conferir na versão instalada.",
    ),
]


def main() -> int:
    if not FRONTEND.is_dir():
        print(f"Pasta frontend não encontrada: {FRONTEND}", file=sys.stderr)
        return 2

    py_files = sorted(FRONTEND.rglob("*.py"))
    findings: list[tuple[Path, int, str, str]] = []

    for path in py_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            print(f"Erro ao ler {path}: {e}", file=sys.stderr)
            return 2
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for name, pattern, hint in RULES:
                if pattern.search(line):
                    findings.append((path, line_no, name, hint))

    if not findings:
        print(f"Nenhum padrão suspeito encontrado em {FRONTEND}")
        return 0

    print("Padrões suspeitos (revisar manualmente — podem ser falsos positivos):\n")
    for path, line_no, name, hint in findings:
        rel = path.relative_to(ROOT)
        print(f"  {rel}:{line_no}  {name}")
        print(f"    -> {hint}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
