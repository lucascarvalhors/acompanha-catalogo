"""verificar_links.py — o "verificador de links" do robô, como o do portal do SIMOB.

Para cada item do catálogo, acessa o link e registra: estado, código HTTP, data e falhas
seguidas. Um link só vira "quebrado" depois de N falhas seguidas (config.yml), para que
uma instabilidade de um dia não tire um curso do ar.

Estados: ativo · instavel (falhou na última verificação) · quebrado · nao_verificado
Uso:  python coletor/verificar_links.py
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import requests

from comum import Cliente, agora, config, gravar_catalogo, ler_catalogo


def verificar(cli: Cliente, it: dict, limite: int) -> dict:
    ant = it.get("link", {})
    try:
        r = cli.head_ou_get(it["url"])
        ok, http, erro = r.status_code < 400, r.status_code, None
        r.close()
    except requests.RequestException as e:
        ok, http, erro = False, None, type(e).__name__
    falhas = 0 if ok else ant.get("falhas_seguidas", 0) + 1
    estado = "ativo" if ok else ("quebrado" if falhas >= limite else "instavel")
    hist = (ant.get("historico", []) + [{"em": agora(), "ok": ok, "http": http}])[-10:]
    return {**it, "link": {"estado": estado, "http": http, "erro": erro, "verificado_em": agora(), "falhas_seguidas": falhas, "historico": hist}}


def main():
    cfg = config(); cli = Cliente(cfg); cat = ler_catalogo()
    cfg["intervalo_entre_requisicoes_s"] = min(cfg["intervalo_entre_requisicoes_s"], 0.2)   # sites diferentes, em paralelo
    with ThreadPoolExecutor(max_workers=8) as ex:
        cat["itens"] = list(ex.map(lambda i: verificar(cli, i, cfg["falhas_para_quebrado"]), cat["itens"]))
    cat["links_verificados_em"] = agora()
    gravar_catalogo(cat)
    cont = {}
    for i in cat["itens"]:
        cont[i["link"]["estado"]] = cont.get(i["link"]["estado"], 0) + 1
    print("links:", cont)


if __name__ == "__main__":
    main()
