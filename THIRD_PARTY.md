# Componentes de terceiros copiados para o projeto

Copiados sem alteração para `.claude/skills/`, em 2026-11-17. Todos MIT.

| Skill | Origem | Versão copiada |
|---|---|---|
| `find-skills` | https://github.com/vercel-labs/skills (skills/find-skills) | skills CLI 1.9.0 |
| `video-to-shorts-skill` | https://github.com/social-media-skills/video-to-shorts-skill | commit de 2026-11-11 |
| `watch` | https://github.com/bradautomates/claude-video | release 0.3.2 |

Para atualizar: `npx skills add <origem> -g -a claude-code -y` e copiar de
`~/.claude/skills/` para `.claude/skills/`.

O hook SessionStart do `claude-video` NÃO foi adotado: ele só emite um aviso.
O hook do projeto é `.claude/hooks/session-start.sh`.
