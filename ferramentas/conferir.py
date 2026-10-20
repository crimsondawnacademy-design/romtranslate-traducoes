#!/usr/bin/env python3
"""Confere o catálogo: cada tradução em traducoes/<plataforma>/<pasta>/.

    python3 ferramentas/conferir.py                      # sai 1 se algo falhar
    python3 ferramentas/conferir.py --indice index.json  # e grava o índice do site

Só a biblioteca padrão do Python (3.11 ou mais novo). Roda no pull request e,
depois do merge, regrava o index.json que o site lê.
"""

import argparse
import json
import re
import sys
import tomllib
import zlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# O nome que o app grava no manifest (Platform do core) e a pasta de cada um.
PLATAFORMAS = {
    "Nes": "nes",
    "Snes": "snes",
    "Gba": "gba",
    "Nds": "nds",
    "GameCube": "gamecube",
    "Ps1": "ps1",
    "Ps2": "ps2",
    "Psp": "psp",
}
KIB = 1024
MAX_PATCH = 20 * KIB * KIB
MAX_MANIFEST = 64 * KIB
MAX_PERFIL = 256 * KIB
MAX_TABELA = KIB * KIB
# BPS que monta o jogo quase do nada, ou que leva mais da metade dele, e o
# jogo disfarcado de patch: traducao muda texto, nao o arquivo inteiro.
MIN_ORIGINAL = 16 * KIB

SHA256 = re.compile(r"[0-9a-f]{64}")
IDIOMA = re.compile(r"[a-z]{2,3}(-[A-Za-z0-9]{2,8})*")
CODIGO = re.compile(r"[A-Z0-9]{2,12}")
HEX_TBL = re.compile(r"(?:[0-9A-Fa-f]{2}){1,16}")


class Recusa(Exception):
    pass


def varint(dados, i):
    """Número do BPS (beat): 7 bits por byte, o bit alto fecha."""
    n, peso = 0, 1
    while True:
        if i >= len(dados):
            raise Recusa("patch BPS cortado no cabeçalho")
        b = dados[i]
        i += 1
        n += (b & 0x7F) * peso
        if b & 0x80:
            return n, i
        peso <<= 7
        n += peso


def conferir_bps(dados):
    if dados[:4] != b"BPS1":
        raise Recusa("não é um patch BPS (o catálogo só aceita BPS: ele confere o original antes de aplicar)")
    if len(dados) > MAX_PATCH:
        raise Recusa(f"patch com {len(dados)} bytes: o teto é {MAX_PATCH}")
    if len(dados) < 4 + 3 + 12 or zlib.crc32(dados[:-4]) != int.from_bytes(dados[-4:], "little"):
        raise Recusa("patch BPS corrompido (o CRC32 do próprio patch não confere)")
    original, i = varint(dados, 4)
    resultado, i = varint(dados, i)
    if original < MIN_ORIGINAL:
        raise Recusa(f"o patch parte de um original de {original} bytes: não é tradução de um jogo")
    if len(dados) > original // 2:
        raise Recusa("o patch tem mais da metade do tamanho do jogo: parece levar o jogo junto")
    return {
        "source_size": original,
        "source_crc32": f"{int.from_bytes(dados[-12:-8], 'little'):08x}",
        "patched_size": resultado,
        "patch_size": len(dados),
    }


def conferir_tabela(texto):
    for n, linha in enumerate(texto.splitlines(), 1):
        if not linha or linha[0] in "#;":
            continue
        chave, igual, _ = linha.partition("=")
        if not igual or not HEX_TBL.fullmatch(chave):
            raise Recusa(f"linha {n} não é HEX=texto")


def textos(valor):
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, list):
        for v in valor:
            yield from textos(v)
    elif isinstance(valor, dict):
        for v in valor.values():
            yield from textos(v)


def conferir_manifest(m, pasta):
    erros = []

    def texto(campo, maximo, obrigatorio=True):
        v = m.get(campo)
        if v is None and not obrigatorio:
            return None
        if not isinstance(v, str) or not v.strip() or len(v) > maximo:
            erros.append(f"{campo}: texto de 1 a {maximo} caracteres")
            return None
        return v

    def lista(campo, vazia):
        v = m.get(campo)
        if not isinstance(v, list) or (not v and not vazia) or len(v) > 30:
            erros.append(f"{campo}: lista de frases ({'pode ser vazia' if vazia else 'ao menos uma'}, no máximo 30)")
        elif not all(isinstance(x, str) and 0 < len(x) <= 300 for x in v):
            erros.append(f"{campo}: cada item é uma frase de 1 a 300 caracteres")

    texto("title", 120)
    texto("author", 80)
    texto("version", 20)
    texto("notes", 1000, obrigatorio=False)
    lista("checked", vazia=False)
    lista("not_checked", vazia=True)

    plataforma = m.get("platform")
    if plataforma not in PLATAFORMAS:
        erros.append(f"platform: um de {', '.join(PLATAFORMAS)} (o que o app grava no manifest)")
    elif pasta.parent.name != PLATAFORMAS[plataforma]:
        erros.append(f"platform {plataforma}: a pasta tem que estar em traducoes/{PLATAFORMAS[plataforma]}/")

    idioma = m.get("target_locale")
    if not isinstance(idioma, str) or not IDIOMA.fullmatch(idioma):
        erros.append("target_locale: código de idioma, como pt-BR ou es")
        idioma = None
    origem = m.get("source_language")
    if origem is not None and (not isinstance(origem, str) or not IDIOMA.fullmatch(origem)):
        erros.append("source_language: código de idioma, como en ou ja (ou ausente)")
    codigo = m.get("game_code")
    if codigo is not None and (not isinstance(codigo, str) or not CODIGO.fullmatch(codigo)):
        erros.append("game_code: o código do cabeçalho do jogo, de 2 a 12 letras maiúsculas ou dígitos (ou ausente)")

    for campo in ("source_sha256", "patched_sha256"):
        if not isinstance(m.get(campo), str) or not SHA256.fullmatch(m[campo]):
            erros.append(f"{campo}: SHA-256 em 64 dígitos hexadecimais minúsculos")
    if m.get("patch_format") != "BPS":
        erros.append('patch_format: "BPS" (exporte o patch em BPS)')

    contas = {c: m.get(c) for c in ("total_entries", "translated_entries", "reviewed_entries")}
    if not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in contas.values()):
        erros.append("total_entries, translated_entries e reviewed_entries: números inteiros, como o app exporta")
    elif max(contas["translated_entries"], contas["reviewed_entries"]) > contas["total_entries"]:
        erros.append("translated_entries e reviewed_entries não passam de total_entries")

    if any("://" in t for t in textos(m)):
        erros.append("o manifest não leva link (nada de endereço para baixar jogo)")

    sha = m.get("source_sha256")
    if idioma and isinstance(sha, str) and SHA256.fullmatch(sha):
        nome = re.compile(rf"(?:[A-Z0-9]{{2,12}}-)?{sha[:8]}-{re.escape(idioma)}(?:-[a-z0-9]+)*")
        if not nome.fullmatch(pasta.name):
            erros.append(f"nome da pasta: <código>-{sha[:8]}-{idioma} (o código é opcional; depois, -apelido se já houver outra)")
    return erros


def conferir_pasta(pasta):
    """Devolve (item do índice, erros) de uma tradução."""
    erros, patches, tabelas = [], [], []
    for p in sorted(pasta.rglob("*")):
        rel = p.relative_to(pasta).as_posix()
        if p.is_symlink():
            erros.append(f"{rel}: link simbólico não é aceito")
        elif p.is_dir():
            if rel != "tables":
                erros.append(f"{rel}/: só a subpasta tables/ é aceita")
        elif p.suffix.lower() == ".bps" and "/" not in rel:
            patches.append(p)
        elif p.suffix.lower() == ".tbl" and rel.count("/") <= 1 and rel.split("/")[0] in (p.name, "tables"):
            tabelas.append(p)
        elif rel not in ("manifest.json", "perfil.toml"):
            erros.append(
                f"{rel}: arquivo não aceito (só manifest.json, um .bps, perfil.toml e tabelas .tbl;"
                " ROM, BIOS, ISO, .zip e o translations.csv nunca)"
            )
    if len(patches) != 1:
        erros.append(f"precisa de exatamente um patch .bps (achei {len(patches)})")

    item = {"path": pasta.relative_to(pasta.parents[2]).as_posix()}
    if len(patches) == 1:
        try:
            item.update(conferir_bps(patches[0].read_bytes()))
            item["patch"] = f"{item['path']}/{patches[0].name}"
        except Recusa as e:
            erros.append(f"{patches[0].name}: {e}")

    for t in tabelas:
        rel = t.relative_to(pasta).as_posix()
        try:
            if t.stat().st_size > MAX_TABELA:
                raise Recusa(f"maior que {MAX_TABELA} bytes")
            conferir_tabela(t.read_text("utf-8-sig"))
        except (Recusa, UnicodeDecodeError) as e:
            erros.append(f"{rel}: tabela inválida ({e})")
    item["tables"] = [f"{item['path']}/{t.relative_to(pasta).as_posix()}" for t in tabelas]

    perfil = pasta / "perfil.toml"
    item["profile"] = None
    if perfil.is_file():
        try:
            if perfil.stat().st_size > MAX_PERFIL:
                raise Recusa(f"maior que {MAX_PERFIL} bytes")
            dados = tomllib.loads(perfil.read_text("utf-8"))
            nomes = {t.stem for t in tabelas}
            for texto in dados.get("texto", []):
                tabela = texto.get("tabela") if isinstance(texto, dict) else None
                if isinstance(tabela, str) and tabela not in nomes:
                    raise Recusa(f'usa a tabela "{tabela}", que não está na pasta (tables/{tabela}.tbl)')
            item["profile"] = f"{item['path']}/perfil.toml"
        except (Recusa, tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
            erros.append(f"perfil.toml: {e}")

    manifest = pasta / "manifest.json"
    try:
        if manifest.stat().st_size > MAX_MANIFEST:
            raise Recusa(f"maior que {MAX_MANIFEST} bytes")
        m = json.loads(manifest.read_text("utf-8"))
        if not isinstance(m, dict):
            raise Recusa("tem que ser um objeto JSON")
    except FileNotFoundError:
        erros.append("falta o manifest.json")
        return item, erros
    except (Recusa, json.JSONDecodeError, UnicodeDecodeError) as e:
        erros.append(f"manifest.json: {e}")
        return item, erros
    erros += [f"manifest.json: {e}" for e in conferir_manifest(m, pasta)]

    # O índice leva só campos conhecidos: o site mostra o que sabe mostrar.
    for campo in (
        "title", "game_code", "platform", "source_language", "target_locale", "author", "version",
        "notes", "checked", "not_checked", "source_sha256", "patched_sha256", "total_entries",
        "translated_entries", "reviewed_entries", "created_at",
    ):
        if isinstance(m.get(campo), (str, int, list)):
            item[campo] = m[campo]
    return item, erros


def conferir_catalogo(raiz):
    """Devolve (índice, erros) do catálogo inteiro."""
    erros, itens = [], []
    base = raiz / "traducoes"
    pastas = PLATAFORMAS.values()
    for p in sorted(base.glob("*")) if base.is_dir() else []:
        if p.name == ".gitkeep":
            continue
        if not p.is_dir() or p.name not in pastas:
            erros.append(f"traducoes/{p.name}: só pastas de plataforma ({', '.join(pastas)})")
            continue
        for pasta in sorted(p.iterdir()):
            if not pasta.is_dir():
                erros.append(f"traducoes/{p.name}/{pasta.name}: cada tradução é uma pasta")
                continue
            item, problemas = conferir_pasta(pasta)
            erros += [f"{item['path']}: {e}" for e in problemas]
            itens.append(item)
    itens.sort(key=lambda t: (str(t.get("title", "")).casefold(), t["path"]))
    return {"translations": itens}, erros


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raiz", type=Path, default=RAIZ, help="pasta do catálogo (padrão: este repositório)")
    ap.add_argument("--indice", type=Path, help="grava o índice que o site lê (index.json)")
    args = ap.parse_args()

    indice, erros = conferir_catalogo(args.raiz)
    if erros:
        print("\n".join(erros), file=sys.stderr)
        print(f"\n{len(erros)} problema(s). Regras: README.md, seção Enviar.", file=sys.stderr)
        return 1
    if args.indice:
        texto = json.dumps(indice, ensure_ascii=False, indent=1) + "\n"
        args.indice.write_text(texto, "utf-8")
    print(f"catálogo conferido: {len(indice['translations'])} tradução(ões)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
