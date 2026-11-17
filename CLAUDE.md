# Regras de trabalho deste projeto

Este projeto vive no repositório **privado** `nicolasmurilo007-bit/GTA6`
(branch principal: `main`). Ele foi criado a partir de
[harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)
(o "upstream"). O fork público `nicolasmurilo007-bit/MoneyPrinterTurbo` não é
mais usado para trabalho.

## Onde o projeto vive

- O projeto é trabalhado **só em sessões na nuvem** (Claude Code na web/app).
  Não deve existir pasta do projeto no computador do usuário.
- O GitHub é a **única cópia que persiste**. O container da sessão é apagado
  quando a sessão termina; o que não foi enviado com `git push` se perde.

## Ao final de toda modificação

1. `git add` + `git commit` com mensagem clara.
2. `git push -u origin <branch-da-sessão>`.
3. Nunca encerrar uma tarefa com mudanças sem commit ou commits sem push.

## Segurança

- O repositório GTA6 é privado, mas mesmo assim: nunca commitar `config.toml`, chaves de API, tokens
  ou vídeos gerados (`/storage/`). O `config.toml` já está no `.gitignore`.
- Chaves de API ficam nos segredos do ambiente da nuvem, não no código.

## Instalação (comando global `mpt`)

```bash
uv tool install --editable . --python 3.11
```

- `mpt webui --port 8503 --headless` abre a interface web.
- `mpt cli --help` gera vídeos pela linha de comando.
- Por ser `--editable`, o `mpt` usa o código deste checkout: mudanças no
  repositório valem na hora, sem reinstalar.

## Atualizar com o projeto original (upstream)

```bash
git remote add upstream https://github.com/harry0703/MoneyPrinterTurbo.git
git fetch upstream main
git merge upstream/main
```

Este `CLAUDE.md` está no `.gitignore` do upstream; ele foi adicionado com
`git add -f` e continua rastreado normalmente.

## Fluxo do projeto (decidido com o usuário)

**Objetivo:** pegar uma gameplay longa do **GTA 6**, tirar cortes e fazer uma
**narração por cima** que explica o contexto (ex.: o jogador faz uma manobra de
carro e a narração conta como ele chegou nela e por que é difícil). Algumas
falas do próprio jogador ficam no vídeo para complementar.

**Voz da narração:** ElevenLabs, voz **Vilaca - Hype Esports Narrator**
(`voice_id` `VTOydm0boYf1E4rUz1Qx`), português do Brasil, modelo `eleven_v4`.
Teste de custo: uma frase de ~12 s custa ~186 créditos; estimar antes de gerar
em volume.

**Etapas**
1. Receber o vídeo longo (por link; ver limitação de rede abaixo).
2. Achar os momentos: picos de volume do áudio e mudanças bruscas de imagem,
   mais a transcrição das falas do jogador com tempo por palavra.
3. Mostrar a lista de cortes (minuto e resumo) e o usuário escolhe.
4. Escrever o roteiro de narração de cada corte; o usuário aprova o texto.
5. Marcar as falas do jogador que ficam; nelas a narração para. No resto, o
   som do jogo fica mais baixo (ducking) sob a narração.
6. Montar: voz, legenda palavra por palavra, música opcional, 9:16.

**Skills instaladas (globais, `~/.claude/skills`)**
- `find-skills` (vercel-labs/skills): procurar skills. O site skills.sh é
  bloqueado na rede da nuvem; use busca na web.
- `video-to-shorts-skill` (social-media-skills): corte, legenda e enquadramento.
  Escolhe momentos pela fala, então é fraca para gameplay sem comentário.
- `watch` (bradautomates/claude-video): deixa o Claude "ver" o vídeo (quadros
  com tempo + transcrição). Com `GEMINI_API_KEY` o Gemini assiste o vídeo
  inteiro, com áudio. Precisa de `yt-dlp` e `ffmpeg`.

**Limitações conhecidas da nuvem**
- YouTube e Google Drive são bloqueados pela rede do ambiente; `yt-dlp` falha
  com 403 do proxy. Liberar exige mudar a rede do ambiente (Configurações).
- Sem placa de vídeo: transcrição local de vídeo longo é lenta.

**Lacunas a construir (código novo neste repositório)**
- Detector de momentos por áudio/imagem para gameplay.
- Encaixe de tempo: a fala gerada precisa caber no corte.
- Mixagem com ducking e trechos originais do jogador mantidos.
