# HANDOFF: onde paramos

Leia este arquivo junto com o `CLAUDE.md` ao retomar o projeto em outra sessão
ou aparelho. Atualizado em 2026-11-17.

## Como continuar de outro aparelho
O trabalho roda em sessões na nuvem, não no notebook. Para continuar:
1. Abra claude.ai/code (ou o app Claude) e entre na mesma conta.
2. Abra a sessão anterior (o histórico da conversa fica nela) **ou** inicie uma
   sessão nova no repositório `nicolasmurilo007-bit/GTA6` com o ambiente
   **"MoneyPrinterTurbo"** e peça: "leia HANDOFF.md e continue".
3. Uma sessão nova já traz as skills (`.claude/skills`) e o hook de instalação
   (`.claude/hooks/session-start.sh`) porque estão neste repositório.
   O container de uma sessão antiga pode ter sido apagado por inatividade:
   só o que está no GitHub persiste.

## Objetivo
Pegar uma gameplay longa do **GTA 6**, tirar cortes e fazer uma **narração por
cima** explicando o contexto (ex.: o jogador faz uma manobra de carro; a
narração conta como ele chegou nela e por que é difícil). Algumas falas do
próprio jogador ficam no vídeo para complementar. Saída vertical 9:16.

## Decisões já tomadas
- **Voz da narração:** ElevenLabs, **Vilaca - Hype Esports Narrator**,
  `voice_id` `VTOydm0boYf1E4rUz1Qx`, português do Brasil, modelo `eleven_v4`.
  Alternativas ouvidas no teste: Eduardo (`R2wd0DF39XU6eENe9jkF`) e Jonas
  (`wTABSOIKENuRDeLiHYDF`). O usuário escolheu a Vilaca.
- **Abordagem B:** narração nova a partir de roteiro escrito por nós, não troca
  de voz da fala original. O som do jogo fica mais baixo sob a narração e as
  falas escolhidas do jogador tocam originais.
- **Repositório:** privado `nicolasmurilo007-bit/GTA6`. O fork público
  `nicolasmurilo007-bit/MoneyPrinterTurbo` não é mais usado.
- **Base de código:** MoneyPrinterTurbo (harry0703) como fonte de legenda
  palavra por palavra, música e montagem. Ele NÃO corta vídeo longo nem acha
  momentos; isso é código novo.
- **Entrada do vídeo:** por link (preferência do usuário).

## Estado atual
- Feito: `mpt` instalado, skills instaladas, voz escolhida e testada, fluxo
  documentado, hook de instalação criado.
- Teste de voz no ElevenLabs: https://elevenlabs.io/app/flows/daZWPBgadMwU8VAVTNtP
  (3 vozes, mesma frase; cada uma custou 186 créditos).
- **Bloqueio:** a rede do ambiente bloqueia YouTube e Google Drive. O `yt-dlp`
  falha com 403 do proxy. Opções: liberar a rede do ambiente
  (Configurações > Ambientes) ou outro jeito de enviar o arquivo.
- **Ainda não recebemos o link do vídeo.**
- **Transcrição local (Whisper) funciona**: liberamos no ambiente "MoneyPrinterTurbo"
  os endereços do Hugging Face (`huggingface.co`, `cdn-lfs.huggingface.co`,
  `cas-bridge.xethub.hf.co`, `cas-server.xethub.hf.co`, `us.aws.cdn.hf.co`).
  Testado com o modelo `tiny` (2026-11-17). Se um modelo maior (small, large)
  pedir outro endereço, o proxy recusa e o erro lista o host: liberar só esse.
- Rede testada: `generativelanguage.googleapis.com` (Gemini) responde; Groq,
  YouTube, Google Drive, Pexels e `api.elevenlabs.io` direto do container são
  recusados. O ElevenLabs funciona pelo conector, não pelo container.

## Rede (decisão do usuário em 2026-11-17)
Rede do ambiente "MoneyPrinterTurbo" passou a **sem restrição** para o
`yt-dlp` baixar do YouTube e para buscar o áudio do ElevenLabs
(`elevenlabsusercontent.com`). Se voltar para "limitada", re-liberar:
`huggingface.co`, `cdn-lfs.huggingface.co`, `cas-bridge.xethub.hf.co`,
`cas-server.xethub.hf.co`, `us.aws.cdn.hf.co`, `elevenlabsusercontent.com`.

## Primeiro teste
Vídeo: trailer oficial de GTA VI, Rockstar Games Brasil, 1 min 31 s
(https://youtu.be/3JUboYgqIxc). Só teste técnico privado: é conteúdo da
Rockstar; publicar exige autorização ou aceitar risco de bloqueio.
Ângulo: comentar o que cada cena mostra (física, carros), com curiosidade e
gancho.

## Próximos passos
1. Receber o link e resolver o acesso ao arquivo.
2. (Opcional) chave grátis do Gemini (aistudio.google.com/apikey) para a skill
   `watch` ver o vídeo inteiro com áudio.
3. Construir (código novo, em `scripts/` ou pasta própria):
   - detector de momentos por picos de áudio e mudança de imagem;
   - encaixe de tempo da fala gerada no corte;
   - mixagem com ducking e trechos originais do jogador.
4. Apresentar a lista de cortes, escrever os roteiros, o usuário aprova.
5. Estimar custo no ElevenLabs antes de gerar em volume.

## Ambiente na nuvem (para recriar, se precisar)
Ambiente pessoal "MoneyPrinterTurbo", rede limitada com pacotes liberados.
Script de preparação:

```bash
export PATH="$HOME/.local/bin:$PATH"
for d in gta6 GTA6 MoneyPrinterTurbo; do
  if [ -f "$d/pyproject.toml" ]; then
    (cd "$d" && uv tool install --force --editable . --python 3.11)
    break
  fi
done
uv tool install "yt-dlp[default,curl-cffi]" || true
```

Depois de mesclar o hook deste repositório na `main`, o script do ambiente fica
redundante (o hook faz o mesmo).

## Conectores usados
ElevenLabs (vozes e geração), Google Drive (disponível, mas arquivos grandes
não testados). A permissão de uso da conta do ElevenLabs precisa ser
reconectada se for preciso ver o saldo de créditos.

## Skills do projeto (`.claude/skills`)
Terceiros, licença MIT, copiadas sem alteração. Ver `THIRD_PARTY.md`.

## Registro 2026-11-17 (noite): download do YouTube
- Rede do ambiente liberada (sem restrição) e `deno` instalado (`npm i -g deno`).
- Mesmo assim o YouTube responde "Sign in to confirm you're not a bot" para o
  IP da nuvem (`yt-dlp` com e sem `--js-runtimes deno`). Não insistir.
- Não usar cookies da conta Google do usuário (risco de segurança).
- Caminhos que sobram: o usuário envia o arquivo .mp4 (Google Drive via conector,
  ainda não testado com arquivo grande) ou envia por outro meio.

## Registro 2026-11-17: decisões do usuário
- Seguir a opção recomendada em tudo: o `.mp4` do trailer chega pelo Google Drive
  (o usuário baixa e sobe); rede do ambiente de volta para "limitada" com
  `huggingface.co`, `cdn-lfs.huggingface.co`, `cas-bridge.xethub.hf.co`,
  `cas-server.xethub.hf.co`, `us.aws.cdn.hf.co`, `elevenlabsusercontent.com`;
  chave do Gemini adiada.
- Formato do resumo final: opções sempre A, B, C, com A = recomendação.

## Registro 2026-11-17: arquivo recebido e analisado
- O `.mp4` chegou pelo conector do Drive (7,4 MB, 640x360). Análise e proposta
  de 3 cortes em `docs/gta6/teste1-analise.md`.
- Próximo: usuário aprova cortes e roteiros; estimar custo; gerar voz Vilaca;
  montar (layout com fundo desfocado, pois a fonte é 360p).

## Registro 2026-11-17 (noite): primeiro teste renderizado
- Decisões do usuário: cortes e roteiros aprovados, seguir em 360p com fundo
  desfocado, curiosidade só com fonte oficial.
- Pesquisa: "física da água/carros" do GTA VI são só rumores (não confirmados
  pela Rockstar). Fato oficial usado no corte A: lançamento em 19/11/2026,
  estado de Leonida (https://www.rockstargames.com/VI). Não afirmar física
  sem fonte.
- Narração gerada (Vilaca, eleven_v4, 1 take cada): 137 + 170 + 149 = 456
  créditos (~US$ 0,09). Flow: https://elevenlabs.io/app/flows/xK8ZDsf92eHGtRHiiJUo
- Código novo: `tools/gta6/render_clip.py` + `tools/gta6/teste1.json`
  (fundo desfocado, ducking por sidechain, legenda alinhada ao roteiro,
  normalização -14 LUFS). Rodar com o Python do `mpt`.
- Saídas (1080x1920) ficam fora do Git. Corte C: -16,7 LUFS (mais baixo que o
  alvo de -14; ajustar com normalização em duas passagens se incomodar).
- Pendente: o usuário assistir e dar o retorno (voz, volume, legenda, ritmo).

## Registro 2026-11-17: referência de estilo recebida
- O usuário enviou um vídeo de referência (curiosidade narrada com fonte
  citada, legenda palavra por palavra, ~29 cortes/minuto). Medidas e lacunas em
  `docs/gta6/estilo-referencia.md`.
- Isso muda o alvo: o produto é **explicativo curto com fatos e fonte**, não
  cortes de uma gameplay longa com falas do jogador.
- Material do vídeo de referência é de terceiros: usar só como estilo.

## Registro 2026-11-17: busca de material e política de uso
- `skills find` não funciona na nuvem (skills.sh bloqueado). As skills de busca no
  YouTube achadas na web usam `yt-dlp` e falhariam aqui (bloqueio anti-robô).
  Solução usada: provedor `youtube-com` do Firecrawl (Alexandria). Método gravado
  em `.claude/skills/buscar-material/SKILL.md`.
- Melhor fonte de imagem real e longa: "Grand Theft Auto VI: An Extended Look"
  (canal oficial Rockstar Games, 26:49, capturado do jogo no PS5):
  https://www.youtube.com/watch?v=tJbzMqJGH4k . Também: Trailer 1
  (QdBZY2fkU-0, 1:31) e o trailer de lançamento (3JUboYgqIxc).
- Evitar: "concept gameplay" / "fan made" / re-uploads de terceiros.
- **Política Take-Two: uso não comercial é tolerado; monetizar fica fora.** Decisão
  pendente do usuário sobre monetização (ver SKILL buscar-material).

## Registro 2026-11-17: cortes de vídeos de streamers (pergunta do usuário)
Ideia levantada: fazer cortes de gameplays de youtubers (ex.: Alanzoka) e
monetizar. Pesquisa feita:
- Não achei política pública do Alanzoka autorizando canais de cortes. Existem
  vários canais de cortes dele, mas isso não prova autorização.
- Há DUAS camadas de direitos: a do streamer (voz, rosto, comentário, edição) e a
  da publicadora do jogo (ex.: Rockstar: só uso não comercial).
- YouTube (política de monetização, "reused content"): monetiza se houver
  comentário/narração original substancial ou valor educativo/de entretenimento;
  "clipes editados juntos com pouca ou nenhuma narrativa" violam; vale mesmo com
  permissão do criador original; direitos autorais continuam valendo à parte.
  Desde julho/2025 a política de conteúdo "inautêntico" (repetitivo/em massa)
  também vale, independente de como foi feito: vídeos em série quase iguais
  correm risco. Fontes: support.google.com/youtube/answer/1311392 e a resposta
  oficial de julho/2025 sobre políticas do YPP.
- Não conferi os requisitos atuais de entrada no Programa de Parcerias.
- Não é aconselhamento jurídico.

## Registro 2026-11-17: TikTok (regras conferidas nas páginas oficiais, ago-set/2026)
- Creator Rewards Program está aberto no Brasil (também EUA, Reino Unido,
  Alemanha, Japão, Coreia do Sul, França, México). Exige: conta pessoal, 18+,
  >=10.000 seguidores, >=100.000 visualizações de vídeo em 30 dias, vídeos
  >=1 minuto, "original e de alta qualidade, filmado, desenhado e produzido
  inteiramente por você", >=1.000 visualizações qualificadas no For You.
  Não contam como original: Duet/Stitch, lip sync, música com direitos >1 min.
  Inferência (não é texto literal): vídeo feito com imagens de terceiros
  (Rockstar, streamers) dificilmente se qualifica.
- Diretrizes (vigentes desde 24/09/2026): proíbem repostar material com direitos
  autorais sem permissão; conteúdo "não original ou reutilizado sem nada novo"
  fica fora do For You (menos alcance).
- IA: TikTok exige rotular conteúdo gerado/muito editado por IA com cenas ou
  pessoas realistas e pede rótulo para áudio realista gerado por IA. Ligar a
  opção "Conteúdo gerado por IA" ao postar vídeos com a voz do ElevenLabs.
  YouTube também exige divulgar conteúdo realista alterado ou sintético.
- Qualquer uso comercial (TikTok Shop, afiliados, patrocínio) conflita com a
  política da Take-Two (só uso não comercial das imagens do jogo).
- Fontes: tiktok.com/creator-academy (Creator Rewards), support.tiktok.com,
  tiktok.com/community-guidelines.

## Registro 2026-11-18: decisões do usuário (todas as opções A/recomendadas)
- Publicar no TikTok e no YouTube Shorts, **sem monetizar** no início; rótulo de
  IA sempre ligado (TikTok) e aviso de conteúdo sintético (YouTube).
- Caminho de conteúdo: explicativos com narração nossa e imagens oficiais; deixar
  o Alanzoka de lado por enquanto (só voltar com autorização por escrito).
- Material de imagem: o usuário sobe o "An Extended Look" (720p) no Drive. AINDA
  NÃO CHEGOU (em 18/11 só o trailer está no Drive).
- Tema do 1º vídeo: fato oficial com fonte (ver opções abaixo).

## Temas com fonte oficial (Rockstar)
- A (recomendado): **trilha adaptativa**. Site oficial (rockstargames.com/VI/music):
  a trilha original é de Justice (dupla francesa vencedora do Grammy, Gaspard
  Augé e Xavier de Rosnay), "adaptive score" ajustada dinamicamente a como o
  jogador interage com Vice City e Leonida; lançamento da trilha em 11 de
  dezembro; rádio com "a maior e mais variada seleção de rádio e podcasts" da
  série, de Classic Rock a Talk Radio.
- B: **contagem final**: pre-load começou em 10/11; lançamento 19/11/2026;
  "The Festival" em 21/11 no Mana Wynwood, Miami (newswire de 09/11).
- C: **as "redes sociais" de Vice City** (observação visual do trailer; não é
  fato oficial; dizer que é observação).
- Newswire oficial: https://www.rockstargames.com/newswire

## Pipeline v2 (estilo da referência)
- `tools/gta6/render_video.py` + `tools/gta6/exemplo_v2.json`: locução contínua,
  planos de ~2,2 s, legenda de uma palavra (alinhada ao roteiro), barras que
  estendem as bordas do plano (fonte <1080p) ou tela cheia (>=1080p), som do jogo
  baixo e abaixando sob a voz, -14 LUFS. Testado só com trailer 360p e a narração
  do teste 1 (sem custo de créditos).
- Pendente: fonte condensada (o servidor só tem DejaVu/Inter/Liberation Sans, sem
  versão condensada: cai numa fonte comum em negrito itálico); cartões de fonte
  (print com frase destacada); setas/mapa.

## Registro 2026-11-18: agentes e plano de automação
- Pedido do usuário: um agente por função (legenda, roteiro, título, descrição...),
  clipes do Alanzoka mantendo o formato de créditos do exemplo, e automação de
  ponta a ponta: perceber o momento na live -> produzir -> postar.
- Criados: 11 agentes em `.claude/agents/` (cacador-de-momentos, gancho,
  roteirista, legendas, titulo, descricao-hashtags, creditos-e-direitos, capa,
  editor-de-video, qualidade, publicador), a skill `produzir-clipe` (roteiro que a
  sessão principal executa; subagentes não chamam subagentes) e
  `docs/gta6/automacao.md` (ferramentas por etapa, limites, regras de API).
- Os agentes novos só carregam em uma sessão nova (ou /agents). Não foram testados.
- Plugin Social Media Skills ficou ativo; Posty sugerido (não confirmado instalado).
- Não existe provedor da Twitch no catálogo do Firecrawl: precisa API Helix com
  credenciais gratuitas do usuário (client id/secret).
- Pendente: credenciais da Twitch, escolha do publicador (Upload-Post/Posty/
  Ayrshare), modo de rodar sem sessão ligada (agendado), autorização do Alanzoka.

## Registro 2026-11-18: decisões B/A/A e primeiro corte de live
- Decisões do usuário: (1) direitos do Alanzoka: seguir só com o formato de
  créditos, assumindo o risco (o Claude tinha recomendado pedir autorização);
  (2) rodar por tarefa agendada de 1 h, começando semiautomático; (3) postar pelo
  Upload-Post. Detalhes e preços em `docs/gta6/automacao.md`.
- Upload-Post (site, 18/11): Free US$0 (10 posts/mês, 2 perfis); Basic US$16/mês
  (ilimitado, 5 perfis). Falta confirmar: TikTok sai público ou rascunho e qual plano
  dá API.
- Twitch SEM credenciais: `yt-dlp` lista/baixa clipes pela GraphQL pública. Hosts
  liberados no ambiente: gql.twitch.tv e d1ndex63qxojbr.cloudfront.net (CDN dos
  clipes). Testado: listou clipes do Alanzoka e baixou um (52 s, 2560x1440 60 fps).
  VODs ainda não testados (CDN com subdomínios variáveis).
- Primeiro corte real feito: clipe "gta 6" do Alanzoka (talk, câmera + chat) ->
  `tools/gta6/render_video.py` modo "corte" (`exemplo_corte.json`: recorte da câmera
  em medidas PARES, gancho no topo, legenda de 1 palavra). Aviso: recorte de largura
  ímpar derrubou o ffmpeg (corrigido no script). Enviado ao usuário, NÃO postado.
- Limitação do layout atual: a câmera ocupa só ~1/3 da altura. Ideias: recorte mais
  fechado no rosto (fonte 1440p aguenta) ou câmera em cima + chat embaixo.
- NÃO criei a tarefa agendada ainda: faltam conta e chave do Upload-Post, TikTok e
  YouTube conectados lá, e 1 clipe postado de ponta a ponta com aprovação.
