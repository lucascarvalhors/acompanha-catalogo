"""comum.py — peças usadas por todos os passos do robô.

O robô NUNCA decide a que competência um curso pertence: ele só coleta, padroniza,
verifica o link e, no máximo, sugere. Quem decide é o especialista, na plataforma.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import unicodedata
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

import requests
import yaml

RAIZ = Path(__file__).resolve().parents[1]
CATALOGO = RAIZ / "dados" / "catalogo.json"
PUBLICADO = RAIZ / "docs" / "catalogo.json"          # o que a página de status e a plataforma leem


def config() -> dict:
    cfg = yaml.safe_load((RAIZ / "config.yml").read_text(encoding="utf-8"))
    if os.environ.get("ACOMPANHA_TESTE"):          # o teste local não precisa esperar entre requisições
        cfg["intervalo_entre_requisicoes_s"] = 0.05
    return cfg


def agora() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalizar_url(url: str) -> str:
    """Remove fragmentos e parâmetros de rastreamento, para não duplicar o mesmo curso."""
    p = urlparse(url.strip())
    q = "&".join(x for x in p.query.split("&") if x and not x.lower().startswith(("utm_", "fbclid", "gclid")))
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", "", q, ""))


def id_item(url: str) -> str:
    """Identificador estável: o mesmo link gera sempre o mesmo id, em qualquer conta ou máquina."""
    return hashlib.sha1(normalizar_url(url).encode("utf-8")).hexdigest()[:12]


def sem_acento(t: str) -> str:
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()


class Cliente:
    """HTTP educado: identifica o robô, respeita robots.txt e espera entre requisições."""

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.s = requests.Session()
        self.s.headers["User-Agent"] = f'{cfg["user_agent"]} contato: {cfg["contato"]}'
        self.robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self._ultimo = 0.0

    def permitido(self, url: str) -> bool:
        base = "{0.scheme}://{0.netloc}".format(urlparse(url))
        if base not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                r = self.s.get(base + "/robots.txt", timeout=self.cfg["tempo_limite_s"])
                rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            except requests.RequestException:
                rp.parse([])
            self.robots[base] = rp
        return self.robots[base].can_fetch(self.s.headers["User-Agent"], url)

    def _esperar(self):
        falta = self.cfg["intervalo_entre_requisicoes_s"] - (time.time() - self._ultimo)
        if falta > 0:
            time.sleep(falta)
        self._ultimo = time.time()

    def get(self, url: str, **kw) -> requests.Response:
        if not self.permitido(url):
            raise PermissionError(f"robots.txt não permite ler {url}")
        self._esperar()
        return self.s.get(url, timeout=self.cfg["tempo_limite_s"], **kw)

    def head_ou_get(self, url: str) -> requests.Response:
        """Para verificar link: HEAD é leve; se o site recusa HEAD, tenta GET."""
        self._esperar()
        try:
            r = self.s.head(url, timeout=self.cfg["tempo_limite_s"], allow_redirects=True)
            if r.status_code in (403, 405, 400, 501):
                raise requests.RequestException("HEAD recusado")
            return r
        except requests.RequestException:
            return self.s.get(url, timeout=self.cfg["tempo_limite_s"], allow_redirects=True, stream=True)


def ler_catalogo() -> dict:
    if CATALOGO.exists():
        return json.loads(CATALOGO.read_text(encoding="utf-8"))
    return {"gerado_em": None, "fontes": [], "itens": []}


def gravar_catalogo(cat: dict) -> None:
    cat["gerado_em"] = agora()
    cat["itens"].sort(key=lambda i: (i.get("fonte", ""), sem_acento(i.get("titulo", ""))))
    txt = json.dumps(cat, ensure_ascii=False, indent=1)
    CATALOGO.write_text(txt, encoding="utf-8")
    PUBLICADO.parent.mkdir(exist_ok=True)
    PUBLICADO.write_text(txt, encoding="utf-8")


def absoluto(base: str, href: str) -> str:
    return urljoin(base, href or "")
