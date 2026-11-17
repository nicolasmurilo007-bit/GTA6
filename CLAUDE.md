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
