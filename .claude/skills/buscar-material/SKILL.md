---
name: buscar-material
description: Procura vídeos por nicho no YouTube (ex.: gameplay e trailers de GTA 6) para usar como material dos clipes narrados, sem baixar nada. Use quando o usuário pedir para achar vídeos, gameplay, trailers ou fontes de imagem de um jogo ou tema.
---

# Buscar material de vídeo por nicho

O container da nuvem NÃO consegue pesquisar nem baixar do YouTube com `yt-dlp`
(bloqueio "Sign in to confirm you're not a bot" para IPs de datacenter).
Pesquisar é possível pelo provedor de dados do Firecrawl, que roda do lado deles.

## Como buscar
Ferramenta: `mcp__Firecrawl__alexandria_library_read`, provedor `youtube-com`.

- Buscar: capability `videos/search_videos`, options
  `{"query": "...", "upload_date": "month|week|year", "sort": "relevance|view_count"}`
  (~20 resultados por página; paginar com `continuation`). Traz id, título, canal,
  duração, visualizações, "há quanto tempo".
- Detalhes de um vídeo: `videos/video_details` (`{"video_id": "..."}`): duração
  exata, data, descrição, idiomas de legenda.
- Transcrição: `videos/video_transcript` (útil para achar fatos e minutos).
- Canal: `videos/resolve_channel` + `videos/channel_videos`.
- Contratos completos: `alexandria_library_search` com
  `cat /library/*/youtube-com/videos/<capability>.md`. Custa ~5 créditos por busca.

## Como escolher
1. **Canal oficial primeiro** (ex.: Rockstar Games, PlayStation, Xbox). Preferir o
   upload original, não cópias/regravações de canais de terceiros.
2. **Evitar "concept gameplay", "fan made", "leak"**: não é imagem real do jogo.
3. Preferir vídeos longos de **imagem do jogo** (ex.: "An Extended Look", capturado
   do jogo no PS5) para tirar muitos planos; trailers curtos para planos-chave.
4. Para **fatos e curiosidades**, usar vídeos/artigos de terceiros só como PISTA e
   confirmar em fonte primária (Rockstar, entrevistas). Citar a fonte no roteiro.
5. Conferir o aviso de direitos: o material é da Rockstar/Take-Two.

## Receber o arquivo
O arquivo só chega à sessão por: conector do Google Drive
(`download_file_content`, grava em disco), upload direto na conversa, ou rede
liberada. O usuário baixa e sobe o .mp4 (recomendar 1080p). Não pedir cookies da
conta Google.

## Política da Rockstar/Take-Two sobre usar imagens do jogo (conferida em 2026-11-17)
Fonte: https://support.rockstargames.com/articles/7bNaeoMFTV0iUDGhStTXvz/policy-on-posting-copyrighted-rockstar-games-material
(atualizada em 10/01/2025).
- A Take-Two em geral **não se opõe a uso NÃO COMERCIAL**, sem spoiler intencional
  de enredo. "Não comercial" = **não ganhar dinheiro com as imagens** postadas nem
  usá-las para promover produto ou serviço.
- Pode remover o conteúdo **a qualquer momento**.
- Não vale para quem produz conteúdo comercial; licença só caso a caso, pedido para
  copyright@take2games.com, com descrição do uso.
- Cenas de "entretenimento dentro do jogo" (TV, shows de comédia) isoladas são
  removidas.
- **Consequência**: canal monetizado ou com publicidade/venda de algo está fora da
  política. Antes de publicar, decidir entre canal sem monetização ou pedir licença.
