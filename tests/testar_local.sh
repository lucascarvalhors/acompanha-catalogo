#!/usr/bin/env bash
# Teste de ponta a ponta sem internet: sobe um site falso local e roda os três passos.
set -e
export ACOMPANHA_TESTE=1
cd "$(dirname "$0")/.."
rm -f dados/catalogo.json docs/catalogo.json
python3 -m http.server 8765 --directory tests/fixtures/site >/dev/null 2>&1 & SRV=$!
trap "kill $SRV" EXIT
sleep 1
python3 coletor/coletar.py --fontes tests/fontes_teste.yml
python3 coletor/verificar_links.py
python3 coletor/verificar_links.py           # segunda verificação: o 404 passa de "instavel" a "quebrado"
python3 coletor/sugerir.py
