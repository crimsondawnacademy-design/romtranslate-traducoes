#!/usr/bin/env python3
"""Confere o conferir.py num catálogo inventado (nenhum byte de jogo):
uma tradução certa passa e cada jeito de errar é recusado.

    python3 ferramentas/teste.py
"""

import json
import random
import shutil
import sys
import tempfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conferir  # noqa: E402


def vi(n):
    out = bytearray()
    while True:
        x, n = n & 0x7F, n >> 7
        if not n:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def crc(b):
    return zlib.crc32(b).to_bytes(4, "little")


def bps(original, resultado, acoes):
    corpo = b"BPS1" + vi(len(original)) + vi(len(resultado)) + vi(0) + acoes + crc(original) + crc(resultado)
    return corpo + crc(corpo)


ORIGINAL = random.Random(7).randbytes(64 * 1024)
NOVO = b"Aperte START!" * 8
RESULTADO = ORIGINAL[:1000] + NOVO + ORIGINAL[1000 + len(NOVO):]
# SourceRead(1000), TargetRead(novo), SourceRead(resto)
ACOES = vi(999 << 2) + vi((len(NOVO) - 1) << 2 | 1) + NOVO + vi((len(ORIGINAL) - 1000 - len(NOVO) - 1) << 2)
SHA = "ab12cd34" + "0" * 56
MANIFEST = {
    "project": "RomTranslate Studio",
    "manifest_version": 1,
    "source_sha256": SHA,
    "patched_sha256": "f" * 64,
    "source_language": "en",
    "target_locale": "pt-BR",
    "platform": "Gba",
    "adapter": "gba",
    "patch_format": "BPS",
    "total_entries": 120,
    "translated_entries": 118,
    "reviewed_entries": 20,
    "created_at": "2026-10-19T12:00:00Z",
    "title": "Brisa e o Farol de Papel",
    "game_code": "BRSA",
    "author": "Fulana",
    "version": "1.0",
    "checked": ["Título, menu e a primeira hora vistos no emulador"],
    "not_checked": ["Final do jogo"],
}
PERFIL = '[[texto]]\nnome = "banco"\ntabela = "letras"\ninicio = 0x100\nfim = 0x200\nterminador = "00"\n'


def catalogo(raiz, mexe=None):
    """Monta traducoes/gba/BRSA-ab12cd34-pt-BR/ e aplica a mudança `mexe`."""
    pasta = raiz / "traducoes" / "gba" / f"BRSA-{SHA[:8]}-pt-BR"
    (pasta / "tables").mkdir(parents=True)
    m = dict(MANIFEST)
    arquivos = {
        "patch.bps": bps(ORIGINAL, RESULTADO, ACOES),
        "perfil.toml": PERFIL.encode(),
        "tables/letras.tbl": b"# letras\n41=A\n61=a\nE6=\\n\n",
    }
    if mexe:
        mexe(m, arquivos, pasta)
    arquivos["manifest.json"] = json.dumps(m).encode()
    for nome, dados in arquivos.items():
        if dados is not None:
            (pasta / nome).write_bytes(dados)
    return conferir.conferir_catalogo(raiz)


def recusa(nome, mexe, trecho):
    with tempfile.TemporaryDirectory() as d:
        _, erros = catalogo(Path(d), mexe)
    assert any(trecho in e for e in erros), f"{nome}: esperava '{trecho}' em {erros}"


def main():
    with tempfile.TemporaryDirectory() as d:
        indice, erros = catalogo(Path(d))
        assert not erros, erros
        [t] = indice["translations"]
        assert t["path"] == f"traducoes/gba/BRSA-{SHA[:8]}-pt-BR", t["path"]
        assert t["patch"].endswith("/patch.bps") and t["profile"].endswith("/perfil.toml")
        assert t["tables"] == [f"{t['path']}/tables/letras.tbl"], t["tables"]
        assert t["source_size"] == len(ORIGINAL) and t["source_crc32"] == f"{zlib.crc32(ORIGINAL):08x}"
        assert t["title"] == MANIFEST["title"] and "adapter" not in t
        # catálogo vazio também passa
        shutil.rmtree(Path(d) / "traducoes" / "gba")
        assert conferir.conferir_catalogo(Path(d)) == ({"translations": []}, [])

    def arquivo(nome, dados):
        return lambda m, a, p: a.update({nome: dados})

    def campo(nome, valor):
        return lambda m, a, p: m.update({nome: valor})

    def sem(nome):
        return lambda m, a, p: m.pop(nome)

    recusa("rom", arquivo("jogo.gba", ORIGINAL), "jogo.gba: arquivo não aceito")
    recusa("csv", arquivo("jogo.pt-BR.translations.csv", b"id,original\n"), "translations.csv: arquivo não aceito")
    recusa("zip", arquivo("tables/x.zip", b"PK"), "tables/x.zip: arquivo não aceito")
    recusa("dois patches", arquivo("outro.bps", b"BPS1"), "exatamente um patch")
    recusa("ips", lambda m, a, p: a.update({"patch.bps": None, "patch.ips": b"PATCHEOF"}), "exatamente um patch")
    recusa("não é bps", arquivo("patch.bps", b"PATCH" + bytes(40) + b"EOF"), "não é um patch BPS")
    ruim = bytearray(bps(ORIGINAL, RESULTADO, ACOES))
    ruim[20] ^= 1
    recusa("crc", arquivo("patch.bps", bytes(ruim)), "corrompido")
    jogo = ORIGINAL[:40000]
    recusa("jogo do nada", arquivo("patch.bps", bps(b"", jogo, vi((len(jogo) - 1) << 2 | 1) + jogo)), "não é tradução")
    recusa(
        "leva o jogo",
        arquivo("patch.bps", bps(ORIGINAL, ORIGINAL, vi((40000 - 1) << 2 | 1) + jogo + vi((len(ORIGINAL) - 40001) << 2))),
        "mais da metade",
    )
    recusa("sem autor", sem("author"), "author:")
    recusa("sem conferido", campo("checked", []), "checked:")
    recusa("sem não conferido", sem("not_checked"), "not_checked:")
    recusa("sha", campo("source_sha256", "ABC"), "source_sha256:")
    recusa("ips no manifest", campo("patch_format", "IPS"), "patch_format")
    recusa("plataforma errada", campo("platform", "Nds"), "traducoes/nds/")
    recusa("plataforma inventada", campo("platform", "Atari"), "platform:")
    recusa("idioma", campo("target_locale", "português"), "target_locale")
    recusa("link", campo("notes", "baixe o jogo em https://exemplo"), "não leva link")
    recusa("contas", campo("translated_entries", 999), "não passam de total_entries")
    recusa("pasta", campo("target_locale", "es"), "nome da pasta")
    recusa("tabela que falta", lambda m, a, p: a.update({"tables/letras.tbl": None}), 'tabela "letras"')
    recusa("tabela torta", arquivo("tables/letras.tbl", b"41=A\nisto nao\n"), "linha 2")
    recusa("perfil torto", arquivo("perfil.toml", b"[[texto]\n"), "perfil.toml:")
    recusa("manifest torto", lambda m, a, p: m.clear() or m.update({"x": float("nan")}), "title:")
    print("teste do conferir: ok")


if __name__ == "__main__":
    main()
