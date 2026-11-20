# Prompt para levar a postagem automática (Upload-Post) a outro repositório

Cole o texto abaixo na sessão do outro projeto (ex.: `comandante-curioso`).

---

Quero automatizar a postagem dos vídeos deste projeto no YouTube usando o Upload-Post, do mesmo jeito que já funciona no meu repositório `nicolasmurilo007-bit/GTA6` (veja lá `tools/gta6/publicar.py`, `docs/gta6/prompt-upload-post-outro-repo.md` e o registro de 20/11/2026 no `HANDOFF.md`). Regras e passos:

**Conta e perfil (já existe conta):**
- Minha conta Upload-Post está no plano GRÁTIS: 2 perfis, 10 envios por mês NO TOTAL (somando todos os canais) e SEM TikTok. O perfil `default` já é do canal "shorts gta6". Este projeto usa o 2º perfil.
- Me peça para criar o perfil deste canal no painel (app.upload-post.com → Users → criar perfil, ex.: `comandante`) e conectar o canal do YouTube nele. Depois confira com a ferramenta `list_users` do conector Upload-Post. Nunca invente nome de perfil.

**Como postar (o que funciona na nuvem):**
- O envio direto pela API no terminal (curl/requests) é BLOQUEADO pelo classificador de segurança da sessão. Use o CONECTOR Upload-Post (ferramentas `mcp__Upload-Post__*`):
  1. `create_media_upload` (nome, `video/mp4`, tamanho exato em bytes);
  2. PUT do arquivo para o `upload_url` com `curl -X PUT -H "Content-Type: video/mp4" --upload-file <arquivo> "<upload_url>"`;
  3. `complete_media_upload` → pega o `media_url`;
  4. `upload_video` SEM `confirmed` (gera a prévia), me mostra a prévia, e só depois da minha aprovação repete com `confirmed: true`.
- Opções do YouTube: `youtubePrivacyStatus` (public/unlisted), `youtubeContainsSyntheticMedia: true` (rótulo de IA sempre ligado, decisão minha), `youtubeSelfDeclaredMadeForKids: false`, `youtubeTags`, `youtubeDefaultLanguage`/`youtubeDefaultAudioLanguage` `pt-BR`, `youtubeCategoryId` adequado.
- Acompanhe com `get_status` se vier `request_id`. Registre cada post em um arquivo `publicacao.json` (link, data, perfil, privacidade).

**Travas (obrigatórias):**
- Nunca postar sem eu dizer "pode postar" para aquele vídeo.
- Antes de postar: o vídeo passou na checagem de qualidade do projeto e tem título, descrição e créditos certos. Nenhuma afirmação falsa na descrição (ex.: não escrever "narração gerada por IA" se não houver).
- Chave de API: se algum script precisar da chave, NUNCA no código nem no chat; use `request_credential` para o host `api.upload-post.com` (cabeçalho `Authorization`, prefixo `ApiKey`). Com o conector, não precisa de chave.
- Se o limite de 10 envios do mês acabar, me avise e pare (não tente de novo).

**Automação (tarefa agendada):**
- Crie a tarefa com `create_trigger` (nova sessão a cada disparo, notificação push, horário de Brasília `CRON_TZ=America/Sao_Paulo`), com um pedido completo e independente: anexar este repositório com `add_repo` se não estiver na sessão, produzir 1 vídeo, me mandar para aprovar, e só postar depois do meu OK. Se não houver material novo, encerrar na hora (economiza meu limite).
- A tarefa criada por aqui NÃO leva o conector Upload-Post (limitação da organização). Me lembre de abrir a rotina em claude.ai → Rotinas e adicionar o conector Upload-Post nela.
- Lembre que o limite de 10 envios/mês é dividido com o canal de GTA 6: combine a frequência comigo antes de ligar.

Faça commit e push ao final de cada mudança e termine cada resposta com o resumo A/B/C (A = sua recomendação).
