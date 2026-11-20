---
name: produzir-clipe
description: Roteiro de produção de ponta a ponta de um clipe (do momento escolhido até o post), chamando os agentes do projeto em ordem. Use quando o usuário pedir para produzir, montar ou postar um clipe ou corte.
---

# Produzir um clipe, passo a passo

Quem executa este roteiro é a sessão principal: subagentes não chamam outros subagentes. Cada etapa grava arquivos em `runs/<AAAA-MM-DD_slug>/` (vídeo e áudio ficam fora do Git).

| # | Etapa | Agente | Entrada -> saída |
|---|---|---|---|
| 1 | Achar o momento | `cacador-de-momentos` | live/VOD/clipes -> `momentos.json` |
| 2 | Aprovação do momento | (usuário, no modo inicial) | escolhe 1 dos candidatos |
| 3 | Gancho | `gancho` | momento -> `gancho.md` |
| 4 | Roteiro/contexto | `roteirista` | momento + gancho -> `roteiro.md`, `fontes.md` |
| 5 | Voz (só explicativo) | ElevenLabs (`estimate_only` antes) | roteiro -> `locucao.mp3` |
| 6 | Legendas | `legendas` | áudio + roteiro -> `legendas.ass` |
| 7 | Montagem | `editor-de-video` | tudo -> `final.mp4`, `edicao.md` |
| 8 | Título | `titulo` | -> `titulo.md` |
| 9 | Descrição e hashtags | `descricao-hashtags` | -> `descricao.md` |
| 10 | Capa | `capa` | `final.mp4` -> `capa.png` |
| 11 | Qualidade | `qualidade` | `final.mp4` -> `qa.json` |
| 12 | Créditos e direitos | `creditos-e-direitos` | tudo -> `checklist.json` |
| 13 | Aprovação final | (usuário) | vê o vídeo e o checklist |
| 14 | Publicar | `publicador` | só com 11 e 12 APROVADOS -> `publicacao.json` |

Regras do roteiro:
- Etapas 3, 4 e 6 podem rodar em paralelo depois da 1/2; 8, 9 e 10 podem rodar em paralelo depois da 7.
- Estimar custo do ElevenLabs antes de gerar e respeitar o teto por clipe definido em `docs/gta6/automacao.md`.
- Se `qualidade` ou `creditos-e-direitos` bloquear, voltar ao agente indicado; nunca pular a checagem.
- Postar só com a confirmação do usuário para aquele clipe (modo inicial). A autonomia só aumenta depois de N clipes aprovados seguidos, decisão registrada em `docs/gta6/automacao.md`.
- Terminar sempre com o resumo A/B/C da regra global do `CLAUDE.md`.


## Modo rápido (scripts + agentes em paralelo)
Python do mpt: `PY="$(uv tool dir)/mpt/bin/python"`.
1. `cacador-de-momentos` lista os clipes recentes e escolhe (devolve a URL).
2. `"$PY" tools/gta6/prepare.py --source <URL> --streamer <nome> --run-dir runs/<AAAA-MM-DD_slug>`: baixa, transcreve (cache), mede rosto/volume, gera `contexto.json`, `clipe.json` e quadros. **Um comando, nada repetido.**
3. **Em paralelo (uma mensagem, 3 chamadas):** `gancho`, `legendas` (correções + `emphasis`) e `efeitos` (sfx/zooms/freezes/annotations). Todos leem `contexto.json`.
4. Montar o `clipe.json` com as respostas -> `editor-de-video` renderiza `final.mp4`.
5. `python tools/gta6/qa.py final.mp4` (agente `qualidade`, modelo leve). Reprovou: corrigir e repetir.
   Depois `python tools/gta6/auditoria.py --config clipe.json --workdir source --video final.mp4 --out auditoria` (legenda x áudio, volume dos SFX, marcações em 4 instantes) e OLHAR as 3 folhas. Erro encontrado: voltar ao agente que o causou e registrar a lição no arquivo dele (`.claude/agents/<agente>.md`, seção "Cobrança").
6. **Em paralelo:** `titulo`, `descricao-hashtags`, `capa`. Depois `creditos-e-direitos`.
7. Mostrar ao usuário o vídeo + checklist e esperar a aprovação antes do `publicador`.
Layouts: conversa = recorte quadrado no streamer; gameplay com câmera sobreposta = `stack` (câmera em cima, gameplay embaixo, `caption_y` 1000, `subs_y` 1180, `hook_y` 700). Base pronta: `runs/2026-11-18_alanzoka_que-isso-rockstar/clipe.json` e `runs/2026-11-18_alanzoka_gta6-vs-zelda/clipe.json`.
Tempos medidos (CPU, sem placa de vídeo): `prepare` ~50 s para um clipe de 52 s; render ~20-30 s; re-render com transcrição em cache bem mais rápido.
