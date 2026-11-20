#!/usr/bin/env python3
"""Publica um clipe aprovado via Upload-Post (https://docs.upload-post.com).

Travas (nada sai sem elas):
  - runs/<id>/qa.json com veredito APROVADO;
  - runs/<id>/checklist.json (agente creditos-e-direitos) sem BLOQUEADO;
  - --aprovado-pelo-usuario (o usuário viu o vídeo e disse que pode postar);
  - sem --enviar, só mostra o que seria enviado (simulação).

A chave NÃO fica no código nem no repositório: ela é guardada como segredo do ambiente
da nuvem para o host api.upload-post.com, e o proxy da sessão a coloca no cabeçalho
`Authorization: Apikey ...`. Por isso o script manda um valor de enfeite.

Uso:
  python tools/gta6/publicar.py runs/<id> --perfil <usuario-upload-post> --plataformas youtube,tiktok
  python tools/gta6/publicar.py runs/<id> --perfil ... --aprovado-pelo-usuario --enviar
Registra o resultado em runs/<id>/publicacao.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.upload-post.com/api/upload"


def first_title(run: Path) -> str:
    md = (run / "titulo.md").read_text(encoding="utf-8")
    # 1ª linha de texto depois do cabeçalho da opção recomendada
    m = re.search(r"###\s*A[^\n]*\n+([^\n(]+)", md)
    return (m.group(1) if m else md.splitlines()[0]).strip()


def public_description(run: Path) -> str:
    """Texto público: o bloco sob "## Texto para publicar" (até a linha ---), sem notas internas."""
    s = (run / "descricao.md").read_text(encoding="utf-8")
    m = re.search(r"##\s*Texto para publicar\s*\n(.*?)(?:\n---|\Z)", s, re.S)
    body = m.group(1) if m else s
    return "\n".join(l for l in body.splitlines() if l.strip() and "NOTA INTERNA" not in l and not l.startswith("#")).strip()


def gates(run: Path) -> list[str]:
    erros = []
    qa = run / "qa.json"
    if not qa.exists() or json.loads(qa.read_text())["veredito"] != "APROVADO":
        erros.append("qa.json não está APROVADO")
    ck = run / "checklist.json"
    if not ck.exists():
        erros.append("falta checklist.json (agente creditos-e-direitos)")
    elif "BLOQUEADO" in ck.read_text(encoding="utf-8").upper():
        erros.append("checklist.json BLOQUEADO")
    if not (run / "final.mp4").exists():
        erros.append("falta final.mp4")
    return erros


def multipart(fields: list[tuple[str, str]], file_field: str, file_path: Path) -> tuple[bytes, str]:
    b = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields:
        out += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    out += (f"--{b}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{file_path.name}\"\r\n"
            "Content-Type: video/mp4\r\n\r\n").encode()
    out += file_path.read_bytes() + f"\r\n--{b}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={b}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path)
    ap.add_argument("--perfil", required=True, help="nome do perfil (user) no Upload-Post")
    ap.add_argument("--plataformas", default="youtube")
    ap.add_argument("--agendar", help="data/hora ISO 8601 (ex.: 2026-11-21T18:00:00Z); vazio = agora")
    ap.add_argument("--privacidade", default="public", choices=["public", "unlisted", "private"],
                    help="YouTube: public, unlisted (só com o link) ou private")
    ap.add_argument("--aprovado-pelo-usuario", action="store_true")
    ap.add_argument("--enviar", action="store_true", help="sem isto, só simula")
    a = ap.parse_args()

    erros = gates(a.run)
    if not a.aprovado_pelo_usuario:
        erros.append("falta --aprovado-pelo-usuario")
    titulo, desc = first_title(a.run), public_description(a.run)
    fields = [("user", a.perfil), ("title", titulo), ("description", desc)]
    fields += [("platform[]", p.strip()) for p in a.plataformas.split(",") if p.strip()]
    # rótulo de IA SEMPRE ligado (decisão do usuário) e conteúdo não infantil
    fields += [("is_ai_generated", "true"), ("containsSyntheticMedia", "true"),
               ("selfDeclaredMadeForKids", "false"), ("privacyStatus", a.privacidade)]
    fields += [("tags[]", t.lstrip("#")) for t in re.findall(r"#\w+", desc)]
    if a.agendar:
        fields.append(("scheduled_date", a.agendar))
    print(json.dumps({"campos": fields, "video": str(a.run / "final.mp4"), "travas": erros or "ok"}, ensure_ascii=False, indent=2))
    if erros:
        sys.exit("NÃO enviado: " + "; ".join(erros))
    if not a.enviar:
        print("Simulação: nada foi enviado (use --enviar).")
        return
    body, ctype = multipart(fields, "video", a.run / "final.mp4")
    req = urllib.request.Request(API, data=body, method="POST",
                                 headers={"Authorization": "Apikey preenchido-pelo-proxy", "Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.loads(r.read().decode() or "{}")
    rec = {"quando": datetime.now(timezone.utc).isoformat(), "perfil": a.perfil, "campos": fields, "resposta": resp}
    (a.run / "publicacao.json").write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resp, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
