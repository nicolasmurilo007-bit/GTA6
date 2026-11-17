#!/bin/bash
# SessionStart hook: prepara as ferramentas do projeto nas sessões na nuvem.
# - comando global `mpt` (instalação editável deste checkout)
# - `yt-dlp` (download de vídeos por link)
# As skills do projeto (watch, video-to-shorts-skill, find-skills) já vêm
# versionadas em .claude/skills e não precisam de instalação.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"
export PATH="$HOME/.local/bin:$PATH"

# uv é a base de tudo abaixo.
if ! command -v uv >/dev/null 2>&1; then
  python3 -m pip install --quiet uv
fi

# Ferramentas globais: instala só o que falta.
if ! command -v yt-dlp >/dev/null 2>&1; then
  uv tool install "yt-dlp[default,curl-cffi]"
fi

# mpt: só reinstala se algo que decide o que é instalado mudou desde a última
# instalação bem-sucedida. O arquivo de hashes fica dentro da pasta da
# ferramenta, então some junto com ela.
tool_dir="$(uv tool dir)/mpt"
hashes="$tool_dir/.session-start.sha256"
if ! sha256sum --check --status "$hashes" 2>/dev/null; then
  rm -f "$hashes"
  uv tool install --force --editable . --python 3.11
  sha256sum .claude/hooks/session-start.sh pyproject.toml uv.lock > "$hashes" || rm -f "$hashes"
fi

# Garante o PATH para os comandos da sessão.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
