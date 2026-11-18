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
