"""coletar.py — lê as fontes de fontes.yml e atualiza dados/catalogo.json.

Para cada curso, guarda só o que a fonte publica: título, instituição, link, descrição e
carga horária. Itens que somem da fonte não são apagados de imediato: ficam marcados e
saem do catálogo ativo depois de N semanas (config.yml).

Uso:  python coletor/coletar.py            (todas as fontes ativas)
      python coletor/coletar.py --fontes outro.yml
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import yaml
from bs4 import BeautifulSoup

from comum import RAIZ, Cliente, absoluto, agora, config, gravar_catalogo, id_item, ler_catalogo, normalizar_url

LIMPA = lambda t: re.sub(r"\s+", " ", (t or "")).strip()


def item(fonte: dict, titulo: str, url: str, descricao: str = "", carga: str = "", instituicao: str = "") -> dict | None:
    titulo, url = LIMPA(titulo), (url or "").strip()
    if not titulo or not url.startswith(("http://", "https://")):
        return None
    return {"id": id_item(url), "titulo": titulo[:300], "url": normalizar_url(url), "descricao": LIMPA(descricao)[:1200],
            "carga_horaria": LIMPA(carga)[:40], "instituicao": LIMPA(instituicao) or fonte.get("instituicao_padrao", ""),
            "fonte": fonte["nome"]}


def de_manual(fonte, cli, cfg):
    caminho = RAIZ / fonte["arquivo"]
    with open(caminho, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            yield item(fonte, r.get("titulo"), r.get("url"), r.get("descricao"), r.get("carga_horaria"), r.get("instituicao"))


def de_rss(fonte, cli, cfg):
    raiz = ET.fromstring(cli.get(fonte["url"]).content)
    for it in raiz.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        filho = lambda n: next((c for c in it if c.tag.split("}")[-1] == n), None)
        link = filho("link")
        href = (link.get("href") if link is not None and link.get("href") else (link.text if link is not None else "")) or ""
        desc = filho("description") if filho("description") is not None else filho("summary")
        texto_desc = BeautifulSoup(desc.text or "", "html.parser").get_text(" ") if desc is not None else ""
        yield item(fonte, filho("title").text if filho("title") is not None else "", href.strip(), texto_desc)


def de_sitemap(fonte, cli, cfg):
    raiz = ET.fromstring(cli.get(fonte["url"]).content)
    locs = [e.text.strip() for e in raiz.iter() if e.tag.split("}")[-1] == "loc" and e.text]
    filtro = fonte.get("filtro_url", "")
    for url in [u for u in locs if filtro in u][: cfg["max_paginas_por_fonte"]]:
        try:
            pag = BeautifulSoup(cli.get(url).content, "html.parser")   # bytes: a codificação é detectada pelo conteúdo
        except Exception as e:  # uma página ruim não derruba a fonte inteira
            print(f"   aviso: {url}: {e}", file=sys.stderr)
            continue
        meta = pag.find("meta", attrs={"name": "description"}) or pag.find("meta", attrs={"property": "og:description"})
        titulo = (pag.find("meta", attrs={"property": "og:title"}) or {}).get("content") if pag.find("meta", attrs={"property": "og:title"}) else (pag.title.string if pag.title else "")
        yield item(fonte, titulo, url, meta.get("content", "") if meta else "")


def de_html(fonte, cli, cfg):
    pag = BeautifulSoup(cli.get(fonte["url"]).content, "html.parser")
    for bloco in pag.select(fonte["seletor_item"])[: cfg["max_paginas_por_fonte"]]:
        t = bloco.select_one(fonte.get("seletor_titulo", "h3"))
        a = bloco.select_one(fonte.get("seletor_link", "a"))
        d = bloco.select_one(fonte["seletor_descricao"]) if fonte.get("seletor_descricao") else None
        yield item(fonte, t.get_text(" ") if t else "", absoluto(fonte["url"], a.get("href")) if a else "", d.get_text(" ") if d else "")


LEITORES = {"manual": de_manual, "rss": de_rss, "sitemap": de_sitemap, "html": de_html}


def main(arq_fontes: str):
    cfg = config()
    fontes = yaml.safe_load((RAIZ / arq_fontes).read_text(encoding="utf-8"))["fontes"]
    cli = Cliente(cfg)
    cat = ler_catalogo()
    antigos = {i["id"]: i for i in cat["itens"]}
    vistos, resumo = {}, []
    for f in [f for f in fontes if f.get("ativo")]:
        n, erro = 0, None
        try:
            for it in LEITORES[f["tipo"]](f, cli, cfg):
                if it and it["id"] not in vistos:
                    vistos[it["id"]] = it; n += 1
        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
            print(f"ERRO na fonte {f['nome']}: {erro}", file=sys.stderr)
        resumo.append({"nome": f["nome"], "tipo": f["tipo"], "itens": n, "erro": erro, "lido_em": agora()})
        print(f"{f['nome']}: {n} itens" + (f" (erro: {erro})" if erro else ""))
    # fontes que falharam não "apagam" seus itens: mantêm-se os antigos dessa fonte
    falhas = {r["nome"] for r in resumo if r["erro"]}
    itens, hoje = [], agora()
    for iid, novo in vistos.items():
        velho = antigos.get(iid, {})
        itens.append({**velho, **novo, "primeira_coleta": velho.get("primeira_coleta", hoje), "ultima_vez_na_fonte": hoje, "ausente_da_fonte": False})
    semanas = cfg["semanas_ausente_para_arquivar"]
    for iid, velho in antigos.items():
        if iid in vistos:
            continue
        if velho.get("fonte") in falhas:
            itens.append(velho); continue
        ultima = datetime.fromisoformat(velho.get("ultima_vez_na_fonte", hoje))
        if (datetime.now(timezone.utc) - ultima).days <= semanas * 7:
            itens.append({**velho, "ausente_da_fonte": True})       # ainda guardado, marcado
    cat.update({"fontes": resumo, "itens": itens, "operador": cfg["operador"]})
    gravar_catalogo(cat)
    print(f"catálogo: {len(itens)} itens ({sum(1 for i in itens if i.get('ausente_da_fonte'))} ausentes da fonte)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--fontes", default="fontes.yml")
    main(ap.parse_args().fontes)
