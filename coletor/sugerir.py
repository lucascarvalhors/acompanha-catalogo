"""sugerir.py — sugere competências para ajudar o especialista. NÃO decide nada.

Compara o título e a descrição de cada curso com as palavras-chave de dados/competencias.json
e grava até 3 sugestões, com os termos encontrados, no campo "sugestoes_robo". A plataforma
mostra essas sugestões ao especialista como ponto de partida; o estudante nunca as vê.
Sem modelo de linguagem, sem conta e sem chave de API.

Uso:  python coletor/sugerir.py
"""
from __future__ import annotations

import json
import re

from comum import RAIZ, gravar_catalogo, ler_catalogo, sem_acento

COMP = {k: v for k, v in json.loads((RAIZ / "dados" / "competencias.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}


def sugerir(it: dict) -> list[dict]:
    texto = " " + sem_acento(f'{it.get("titulo", "")} {it.get("titulo", "")} {it.get("descricao", "")}') + " "   # título conta em dobro
    res = []
    for c, d in COMP.items():
        achados = [t for t in d["termos"] if re.search(r"\b" + re.escape(sem_acento(t)) + r"\b", texto)]
        if achados:
            res.append({"competencia": int(c), "nome": d["nome"], "termos": achados, "pontos": sum(texto.count(sem_acento(t)) for t in achados)})
    return sorted(res, key=lambda r: -r["pontos"])[:3]


def main():
    cat = ler_catalogo()
    for it in cat["itens"]:
        it["sugestoes_robo"] = sugerir(it)
    gravar_catalogo(cat)
    print("com sugestão:", sum(1 for i in cat["itens"] if i["sugestoes_robo"]), "de", len(cat["itens"]))


if __name__ == "__main__":
    main()
