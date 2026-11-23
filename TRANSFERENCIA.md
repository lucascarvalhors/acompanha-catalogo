# Transferir o robô para o PMG / TI da UFRGS

Nada do robô está preso a uma pessoa: não há senha, chave de API nem segredo no repositório.
O que identifica o dono são só três coisas: **a conta dona do repositório**, **o endereço do
GitHub Pages** e **os contatos em `config.yml`**.

## Opção A — transferir o repositório (recomendada: mantém histórico e rotinas)
1. A TI cria (ou indica) uma **organização** no GitHub, por exemplo `pmg-ufrgs`, e convida a dona
   atual do repositório como membro com permissão para criar repositórios.
2. No repositório: **Settings › General › Danger Zone › Transfer ownership** › escolha a organização.
3. Na organização: **Settings › Actions › General** › permitir Actions e **Workflow permissions:
   Read and write** (políticas da organização podem bloquear; a TI libera).
4. No repositório transferido: **Settings › Pages** › confirmar *Deploy from a branch* › `main` › `/docs`.
   O endereço passa a ser `https://pmg-ufrgs.github.io/acompanha-catalogo/`.
5. Em `config.yml`: trocar `operador`, `contato` e o endereço em `user_agent`.
6. Na Vercel do Acompanha: trocar **só** `CATALOGO_URL` para o novo endereço e fazer novo deploy.
7. Trocar o `CURADORIA_TOKEN` na Vercel e entregar a nova chave aos especialistas.
8. Rodar **Actions › Coletar catálogo › Run workflow** e conferir a página de status.

## Opção B — começar do zero na conta da instituição
Criar um repositório novo na organização, enviar estes arquivos e seguir o README a partir do passo 3.
O catálogo é recriado na primeira coleta. As decisões dos especialistas **não se perdem**: ficam no
banco da plataforma, ligadas ao id de cada curso, que é calculado a partir do link e é o mesmo em
qualquer conta.

## Depois da transferência
- Remover acessos pessoais que não sejam mais necessários (Settings › Collaborators).
- Se o projeto da Vercel também for para uma equipe institucional, as variáveis `CATALOGO_URL`,
  `CURADORIA_TOKEN` e `DATABASE_URL` vão junto; confira em **Settings › Environment Variables**.
- Definir quem responde pelas fontes (`fontes.yml`) e pela curadoria — o robô mantém os links
  verificados, mas a escolha das fontes e as decisões de competência são trabalho de pessoas.
