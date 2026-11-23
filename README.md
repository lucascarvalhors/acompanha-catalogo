# acompanha-catalogo — robô do catálogo de cursos abertos

O robô **coleta** cursos abertos de fontes públicas, **verifica os links todos os dias** e publica uma
página de status (como a do Portal de Ferramentas Soft Skill do SIMOB). Ele **não decide** a que
competência cada curso pertence: isso é feito por um especialista, na página `curadoria.html` da
plataforma Acompanha. O robô só deixa sugestões, que o especialista pode ignorar.

Não usa modelo de linguagem, chave de API nem conta em provedor de IA. Roda de graça no
GitHub Actions (repositório público) e publica pelo GitHub Pages.

## O que acontece e quando
| Rotina | Quando | O que faz |
|---|---|---|
| **Coletar catálogo** (`.github/workflows/coletar.yml`) | toda segunda, 6h (Brasília) | lê `fontes.yml`, verifica links, sugere competências, grava |
| **Verificar links** (`.github/workflows/verificar.yml`) | todo dia, 7h (Brasília) | só verifica os links e grava |

As duas também rodam na hora: aba **Actions** › escolha a rotina › **Run workflow**.

Estados de link: **ativo** · **instável** (falhou na última verificação) · **quebrado** (falhou
`falhas_para_quebrado` vezes seguidas; padrão 2) · **não verificado**. Curso que some da fonte fica
marcado e sai depois de `semanas_ausente_para_arquivar` semanas.

## Passo a passo (conta pessoal, para fins didáticos)

1. **Conta no GitHub.** Pode ser criada com qualquer e-mail; não precisa de Gmail.
2. **Criar o repositório.** Em github.com › **New repository** › nome `acompanha-catalogo` ›
   **Public** › Create. Depois **Add file › Upload files** e arraste todo o conteúdo desta pasta
   (inclusive a pasta `.github`). Confirme com **Commit changes**.
   Pastas que começam com ponto costumam ficar ocultas no Finder e no Explorador e não sobem no
   arraste. Confira se `.github/workflows/` aparece no repositório; se não aparecer, use
   **Add file › Create new file**, digite o nome `.github/workflows/coletar.yml`, cole o conteúdo do
   arquivo e salve; repita para `verificar.yml`.
3. **Permitir que o robô grave.** **Settings › Actions › General › Workflow permissions** ›
   marque **Read and write permissions** › Save. Sem isso, a rotina roda mas não consegue salvar.
4. **Publicar a página de status.** **Settings › Pages** › *Build and deployment*: Source
   **Deploy from a branch**, Branch **main**, pasta **/docs** › Save. O endereço será
   `https://SEU-USUARIO.github.io/acompanha-catalogo/`.
5. **Identificar o operador.** Edite `config.yml`: `contato` (e-mail de quem responde pelo robô) e
   `user_agent` (troque `SEU-USUARIO`). Os sites de origem veem esses dados em cada acesso.
6. **Escolher as fontes.** Em `fontes.yml`, cada fonte só é lida com `ativo: true`. Para começar sem
   programar, cole cursos em `dados/fontes_manuais.csv` (separador `;`). Para ativar um RSS, sitemap ou
   página, **abra o endereço no navegador antes** e confira se existe; em páginas HTML, os seletores
   (`seletor_item`, `seletor_titulo`…) são os do site real (botão direito › Inspecionar).
7. **Primeira coleta.** **Actions › Coletar catálogo › Run workflow**. Em poucos minutos a página do
   passo 4 mostra os cursos e o estado de cada link.
8. **Ligar à plataforma.** Na Vercel do Acompanha: variáveis `CATALOGO_URL`
   (`https://SEU-USUARIO.github.io/acompanha-catalogo/catalogo.json`) e `CURADORIA_TOKEN` (valor
   aleatório); no Postgres, rode o trecho final do `schema.sql` (tabela `curadoria_oportunidade`);
   faça um novo deploy. O especialista passa a usar `curadoria.html`.

## Testar no próprio computador (sem internet)
```bash
pip install -r requirements.txt
bash tests/testar_local.sh      # sobe um site falso local e roda coleta, verificação e sugestão
```
Abra `docs/index.html` com `python -m http.server --directory docs` para ver a página de status.

## Boas práticas que o robô já segue
- Respeita o `robots.txt` de cada site e espera entre requisições (`intervalo_entre_requisicoes_s`).
- Identifica-se no User-Agent com um contato.
- Uma fonte fora do ar não apaga os cursos dela: os itens antigos são mantidos até a próxima coleta.
- O mesmo link vindo de duas fontes vira um item só (id estável a partir do endereço).

## Atenção
- Repositórios públicos com agendamento podem ter as rotinas pausadas pelo GitHub após um período
  sem atividade. Se a página de status parar de atualizar, confira a aba **Actions** e reative.
- Confira os termos de uso de cada fonte antes de ativá-la. Se a fonte for o portal do SIMOB,
  combine com a equipe dele: o mais simples é eles publicarem a lista e o robô só lê-la.
- Para transferir ao PMG ou à TI da UFRGS, siga `TRANSFERENCIA.md`.
