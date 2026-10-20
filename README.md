# Traduções da comunidade · RomTranslate Studio

[English below](#community-translations--romtranslate-studio)

Traduções de jogos feitas com o [RomTranslate Studio](https://github.com/crimsondawnacademy-design/romtranslate-studio),
pra ninguém traduzir do zero o que alguém já traduziu. Cada tradução é um **patch**: ele guarda a
diferença entre o jogo original e o traduzido, não o jogo. Para usar, você precisa da sua própria
cópia do jogo, a mesma que a tradução indica.

**Lista com busca, por plataforma e idioma:** https://romtranslate-studio.pages.dev/traducoes/

Aqui não há jogos, ROMs, BIOS nem links para baixá-los.

## Usar uma tradução

1. Ache o jogo na lista (no site ou na pasta `traducoes/`).
2. Confira se o seu arquivo é o mesmo da tradução: o SHA-256 dele tem que ser igual ao
   `source_sha256` (no Mac e no Linux, `shasum -a 256 arquivo`; no Windows,
   `certutil -hashfile arquivo SHA256`). O app mostra esse número ao abrir o jogo.
3. Baixe o patch `.bps` e aplique numa cópia do jogo com um aplicador de patch, por exemplo o
   [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/), que roda no navegador sem enviar
   o jogo pra lugar nenhum. O BPS confere o original antes: com outro arquivo, ele recusa.
4. Guarde o original. O patch não serve para outra versão ou região do jogo.

## Enviar a sua tradução

Uma pasta por tradução, em `traducoes/<plataforma>/<código>-<sha8>-<idioma>/`:

- `<plataforma>`: `nes`, `snes`, `gba`, `nds`, `gamecube`, `ps1`, `ps2` ou `psp`;
- `<código>`: o código do cabeçalho do jogo, se ele tiver (ex.: `ABCE`); opcional;
- `<sha8>`: os 8 primeiros dígitos do SHA-256 do arquivo original;
- `<idioma>`: o idioma da tradução, como no app (`pt-BR`, `es`, `en`...).
- Se já existe uma tradução com o mesmo nome, acrescente `-apelido` (ex.: `-fulana`).

Dentro dela vão só estes arquivos:

| Arquivo | O que é |
| --- | --- |
| `manifest.json` | O manifesto que o app exporta junto com o patch (`exports/<jogo>.<idioma>.manifest.json`), renomeado, com os campos abaixo acrescentados. |
| um `.bps` | O patch, **em BPS** (na tela do patch, escolha BPS; no CLI, `romtranslate patch <projeto> --format bps`). |
| `perfil.toml` | Opcional: o perfil do jogo, se ele precisou de um. Com ele, quem vier depois melhora a tradução sem estudar o jogo de novo. |
| `tables/*.tbl` | Opcional: as tabelas de letras que o perfil usa. |

**Nunca:** ROM, BIOS, ISO, arquivo compactado, imagem de tela, o `translations.csv` (ele traz o
texto original do jogo), link para baixar jogo.

Campos que você acrescenta ao manifesto do app:

```json
{
  "title": "Nome do jogo",
  "game_code": "ABCE",
  "author": "Seu nome ou apelido",
  "version": "1.0",
  "checked": ["Título, menus e a primeira hora vistos no emulador"],
  "not_checked": ["Final do jogo", "Textos desenhados em imagem"],
  "notes": "Opcional: o que mais quem for jogar precisa saber."
}
```

`checked` diz o que você viu funcionando; `not_checked`, o que não viu (pode ficar vazio, mas seja
honesto: é o que evita alguém achar que está pronto). `game_code` é opcional.

**Como enviar:** faça um fork deste repositório, adicione a pasta e abra um pull request. Sem usar
git: no seu fork, entre na pasta `traducoes/<plataforma>/`, use **Add file → Upload files** e
escreva o nome da pasta nova no começo de cada arquivo. O pull request roda uma checagem automática;
dá pra rodar antes no seu computador (Python 3.11 ou mais novo, nada a instalar):

```bash
python3 ferramentas/conferir.py
```

A checagem recusa o envio que:

- tem qualquer arquivo fora da lista acima (é assim que ROM, BIOS e o `translations.csv` ficam de fora);
- tem um patch que não é BPS, está corrompido, parte de um original com menos de 16 KiB ou tem mais
  da metade do tamanho do jogo (aí o patch está levando o jogo junto), ou passa de 20 MiB;
- tem manifesto sem algum campo, com SHA-256 malformado, plataforma ou pasta trocada, ou com link;
- tem perfil que não abre ou que usa uma tabela que não está na pasta.

Quem aceita o pull request é o mantenedor, depois de olhar. Ao aceitar, o `index.json` (a lista que o
site lê) é refeito sozinho. Mudança fora de `traducoes/` só vem do mantenedor.

## Aviso legal

- Não somos advogados, e isto não é orientação jurídica.
- Este repositório não tem jogos, ROMs, BIOS nem links para baixá-los. Cada pessoa usa a própria
  cópia do jogo.
- Os nomes dos jogos e as marcas pertencem aos seus donos e aparecem só para dizer a que jogo cada
  patch se aplica. O catálogo não tem ligação com eles.
- Cada tradução é de quem a fez. Quem envia declara que fez a tradução (ou tem permissão de quem fez)
  e aceita que ela seja redistribuída aqui.
- **Pedido de remoção** (de quem tem direitos sobre o jogo ou do autor da tradução): abra uma
  [issue](https://github.com/crimsondawnacademy-design/romtranslate-traducoes/issues) dizendo qual
  pasta. Ela sai do catálogo.
- As ferramentas deste repositório (`ferramentas/`, `.github/`) são MIT, como o app.

---

# Community translations · RomTranslate Studio

Game translations made with [RomTranslate Studio](https://github.com/crimsondawnacademy-design/romtranslate-studio),
so nobody has to translate from scratch what someone already did. Each translation is a **patch**: it
stores the difference between the original game and the translated one, not the game. To use it, you
need your own copy of the game, the same one the translation names.

**Searchable list, by platform and language:** https://romtranslate-studio.pages.dev/en/translations/

There are no games, ROMs, BIOS files or links to download them here.

## Using a translation

1. Find the game in the list (on the site or in the `traducoes/` folder).
2. Check that your file is the one the translation was made for: its SHA-256 must match
   `source_sha256` (macOS and Linux: `shasum -a 256 file`; Windows: `certutil -hashfile file SHA256`).
   The app shows this number when it opens the game.
3. Download the `.bps` patch and apply it to a copy of the game with a patcher, such as
   [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/), which runs in the browser without
   uploading the game. BPS checks the original first: with another file, it refuses.
4. Keep the original. The patch does not work on another version or region of the game.

## Sending your translation

One folder per translation, `traducoes/<platform>/<code>-<sha8>-<language>/` (`code` is the game's
header code, optional; `sha8` is the first 8 digits of the original file's SHA-256; add `-nickname`
if the name is taken). It holds only: `manifest.json` (the manifest the app exports with the patch,
renamed, plus the fields in the example above: `title`, `game_code`, `author`, `version`, `checked`,
`not_checked`, `notes`), one `.bps` patch (choose BPS when exporting), and optionally `perfil.toml`
and the `tables/*.tbl` it uses. **Never** a ROM, BIOS, ISO, archive, screenshot, the
`translations.csv` (it carries the game's original text) or a link to download a game.

Fork, add the folder, open a pull request (without git: **Add file → Upload files** in your fork). An
automatic check runs on it, and you can run it first with `python3 ferramentas/conferir.py` (Python
3.11+, nothing to install; its messages are in Portuguese). It refuses any file outside that list,
a patch that is not BPS, is corrupted, starts from an original under 16 KiB, is more than half the
size of the game or over 20 MiB, a manifest with a missing field, a malformed hash, a wrong platform
folder or a link, and a profile that does not parse or uses a table that is not in the folder.

## Legal notice

We are not lawyers, and this is not legal advice. This repository has no games and no links to them;
everyone uses their own copy. Game names and trademarks belong to their owners and appear only to
say which game a patch applies to; this catalog is not affiliated with them. Each translation belongs
to whoever made it; by sending one, you state you made it (or have permission) and agree to its
redistribution here. **Takedown requests** (from rights holders or translation authors): open an
[issue](https://github.com/crimsondawnacademy-design/romtranslate-traducoes/issues) naming the folder,
and it will be removed. The tools in this repository (`ferramentas/`, `.github/`) are MIT, like the app.
