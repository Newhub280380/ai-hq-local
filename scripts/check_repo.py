"""Минимальные проверки репозитория ai-hq-local.

Проверяет, что репозиторий остаётся в понятном состоянии:
  * README.md существует и начинается с H1-заголовка;
  * каждый .md-файл содержит H1-заголовок;
  * в репозитории нет файлов с секретами.

Запуск:  python scripts/check_repo.py
Код возврата: 0 — всё ок, 1 — есть нарушения.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv"}
SECRET_NAMES = {".env", ".env.local", ".env.production", "secrets.json", "credentials.json"}
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
H1 = re.compile(r"^#\s+\S", re.M)


def repo_files() -> list[str]:
    """Список отслеживаемых git файлов (иначе — обход каталога)."""
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT,
        )
        return [line.strip().replace("\\", "/") for line in res.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.CalledProcessError):
        out = []
        for root, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                out.append(
                    os.path.relpath(os.path.join(root, name), ROOT).replace("\\", "/")
                )
        return out


def main() -> int:
    problems: list[str] = []

    if not (ROOT / "README.md").is_file():
        problems.append("README.md отсутствует")
    else:
        with open(ROOT / "README.md", encoding="utf-8", errors="replace") as fh:
            if not fh.read().lstrip().startswith("# "):
                problems.append("README.md должен начинаться с H1-заголовка")

    for path in repo_files():
        low = path.lower()
        base = os.path.basename(low)
        if base in SECRET_NAMES or low.startswith("secrets/") or low.endswith(SECRET_SUFFIXES):
            problems.append(f"файл с секретами в репозитории: {path}")
        if base.endswith(".md"):
            with open(ROOT / path, encoding="utf-8", errors="replace") as fh:
                if not H1.search(fh.read()):
                    problems.append(f"в {path} нет H1-заголовка")

    if problems:
        print("Проверка репозитория не пройдена:")
        for item in problems:
            print(f"  - {item}")
        return 1

    print(f"OK: проверено файлов — {len(repo_files())}, нарушений нет.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
