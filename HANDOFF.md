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
