# Automação de clipes: agentes, ferramentas e dificuldades

Plano do usuário: assistir a live (ou o VOD), perceber o momento, produzir o clipe
com os agentes e postar, de forma automática. Decisões em vigor: sem monetizar no
início; clipes de streamer mantêm os créditos no formato do exemplo; rótulo de IA
sempre ligado; aprovação humana antes de postar no modo inicial.

## Formato de crédito (copiado do exemplo do usuário)
`<gancho> 😭 assiste até o final 🎥 Créditos: @alanzoka (twitch.tv/alanzoka) #gta6 #gtavi #alanzoka #cortes #gta6brasil`
Aviso registrado: crédito na legenda NÃO é autorização do streamer.

## Agentes do projeto (`.claude/agents/`)
cacador-de-momentos, gancho, roteirista, legendas, titulo, descricao-hashtags,
creditos-e-direitos, capa, editor-de-video, qualidade, publicador.
Roteiro de produção: skill `produzir-clipe`.

## Ferramentas por etapa (pesquisadas em 18/11/2026)
| Etapa | O que usar | Observação |
|---|---|---|
| Achar clipes/VODs do streamer | API Helix da Twitch (clipes por streamer, lista de VODs), `yt-dlp` para baixar VOD/clipe | Precisa de credenciais gratuitas de desenvolvedor (client id/secret). Não há provedor de dados da Twitch no catálogo do Firecrawl |
| Detectar momento | picos de chat + picos de áudio (ffmpeg) + clipes de espectadores; Whisper só na janela candidata | Ferramentas prontas existem como serviço (Eklipse, etc.); não são skills |
| Gancho, roteiro, legenda, título, hashtags | plugin Social Media Skills (hook-writer, caption-writer, hashtag-strategy, youtube-shorts, tiktok-script, platform-specs-and-validation) | Ativo na sessão em 18/11 |
| Voz | ElevenLabs (voz Vilaca) só nos explicativos; cortes usam a voz do streamer | Estimar custo antes |
| Montagem | `tools/gta6/render_video.py`, `render_clip.py` | Pipeline v2 testado em 360p |
| Publicar | Upload-Post (`app/services/upload_post.py`, já no projeto: TikTok, Instagram, YouTube Shorts), Posty, Ayrshare | Preço e limites do Upload-Post NÃO conferidos |

## API oficial do TikTok (conferido)
- Direct Post exige app aprovado com escopo `video.publish`.
- Cliente NÃO auditado: só posta em modo privado (`SELF_ONLY`), máx. 5 usuários por 24 h; para público, é preciso passar por auditoria.
- O app deve enviar o conteúdo só depois do consentimento expresso do usuário e checar `max_video_post_duration_sec`.
- Alternativa: modo `MEDIA_UPLOAD` (envia para a caixa de entrada e o criador finaliza no app).

## YouTube (parcialmente conferido)
- A página oficial de `videos.insert` mostra custo de 1 unidade no "Video Uploads quota bucket".
- NÃO consegui confirmar na documentação atual a regra de que projetos de API não verificados publicam em modo privado até auditoria; confirmar antes de depender disso.

## Limites e tetos (valores iniciais, o usuário pode mudar)
- Máx. 3 posts por dia por plataforma; intervalo mínimo de 3 h; nunca repostar o mesmo clipe.
- Teto de custo de voz por clipe explicativo: 1.200 créditos ElevenLabs (~US$ 0,25).
- Segredos (Twitch, Upload-Post, etc.) só como segredos do ambiente (`request_credential`), nunca no Git.

## Decisões do usuário em 18/11/2026 (B, A, A)
1. **Direitos do Alanzoka:** seguir com cortes mantendo só o formato de créditos do
   exemplo, assumindo o risco (recomendação do Claude era pedir autorização por
   escrito; o usuário escolheu seguir). O agente `creditos-e-direitos` só avisa.
   Mantido: interruptor para parar tudo e registro de origem de cada clipe.
2. **Execução:** tarefa agendada do Claude, a cada 1 h, modo SEMIAUTOMÁTICO (o
   usuário aprova cada clipe antes de postar; aviso por notificação). Só agendar
   depois de os pré-requisitos abaixo estarem prontos.
3. **Publicação:** Upload-Post (já integrado em `app/services/upload_post.py`).

## Upload-Post (conferido em 18/11/2026 no site)
- Free: US$ 0, 10 uploads/mês, 2 perfis. Basic: US$ 16/mês (US$ 192/ano), uploads
  ilimitados, 5 perfis. Professional: US$ 33/mês, 25 perfis. Advanced: US$ 118/mês.
  Business: US$ 350/mês.
- Eles afirmam usar APIs oficiais já verificadas (você não cria app no TikTok nem
  espera revisão). É afirmação do site; não verificada de forma independente.
- NÃO apareceu no site: se o TikTok sai público ou em rascunho, e qual plano
  inclui API. Testar com 1 post antes de assumir.
- Conta: 3 posts/dia x 30 dias = 90 posts/mês: o gratuito (10) não basta; o Basic
  cobre.

## Twitch: como acessar sem credenciais de API (testado)
- `yt-dlp` lista e baixa clipes/VODs pela GraphQL pública `gql.twitch.tv`: NÃO
  precisa de client id/secret da Twitch. O proxy da nuvem recusou `gql.twitch.tv`
  até liberarmos.
- Começar pelos **clipes de espectadores** (curtos, já escolhidos pelo público,
  servidos de poucos hosts). VODs usam subdomínios variáveis de CDN e podem exigir
  rede sem restrição ou outro executor.
- Hosts liberados no ambiente em 18/11: gql.twitch.tv,
  clips-media-assets2.twitch.tv, production.assets.clips.twitchcdn.net (palpite
  de hosts de clipes; ajustar conforme o proxy recusar).

## Pré-requisitos antes de agendar a tarefa horária
1. Conta no Upload-Post + chave de API (segredo do ambiente via request_credential).
2. TikTok e YouTube do usuário conectados na conta do Upload-Post.
3. Teste do download de 1 clipe real do Alanzoka na nuvem.
4. 1 clipe produzido e postado de ponta a ponta com aprovação manual.
