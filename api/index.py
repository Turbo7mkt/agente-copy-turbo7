"""Ponto de entrada da Vercel.

O runtime Python da Vercel procura uma variável ASGI chamada `app` neste
arquivo. Toda a lógica fica em `app/` — aqui só o encaminhamento.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402,F401
