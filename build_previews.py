#!/usr/bin/env python3
"""
Generate PNG preview images for the README & marketplace.

For each category we compose a single SVG that places the relevant icons
(read from ``icons/``) into a labelled grid. The composite SVG is written
to ``previews/*.svg`` and converted to PNG with ``qlmanage`` (macOS).

Two details that need to be right:

  * **XML escaping.** Titles and labels go inside ``<text>`` nodes, so any
    ``&`` / ``<`` / ``>`` *must* be escaped — otherwise ``qlmanage`` parses
    the malformed XML, fails, and writes the rendered error message as the
    PNG.

  * **Square canvas.** ``qlmanage -t -s N`` crops the long side of the
    source to fit an N×N thumbnail. If the SVG is wider than it is tall,
    the right edge gets clipped (visibly: missing columns). We pad the
    canvas to ``max(w, h) × max(w, h)`` so cropping has no effect.

Run: ``python3 build_previews.py``
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ICONS_DIR = ROOT / "icons"
PREVIEWS_DIR = ROOT / "previews"

# Visual constants (kept in sync with build.py / lusitania-theme)
BG = "#0d1620"
PANEL = "#172534"
LABEL = "#c3cee3"
ACCENT = "#80deea"

PADDING = 24
TITLE_H = 56
CELL = 64
ICON_PX = 40
ROW_LABEL_H = 18
COLS = 6                          # picked so 6×4 grids are perfectly square
THUMB_SIZE = 1600                 # qlmanage thumbnail max dimension


# ----- XML helpers ---------------------------------------------------------- #
def _xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def _inner_svg(path: Path) -> str:
    """Return the content of an SVG file without its outer <svg> wrapper."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<\?xml.*?\?>", "", text)
    m = re.search(r"<svg[^>]*>(.*)</svg>\s*$", text, re.DOTALL)
    return m.group(1) if m else text


def _icon_group(name: str, x: float, y: float, size: int = ICON_PX) -> str:
    inner = _inner_svg(ICONS_DIR / f"{name}.svg")
    s = size / 32
    return f'<g transform="translate({x} {y}) scale({s})">{inner}</g>'


# ----- Composite builders --------------------------------------------------- #
def _grid_svg(title: str, items: list[tuple[str, str]]) -> str:
    """Labelled grid, padded to a square canvas so qlmanage won't crop."""
    rows = (len(items) + COLS - 1) // COLS
    content_w = PADDING * 2 + COLS * CELL
    content_h = PADDING + TITLE_H + rows * (CELL + ROW_LABEL_H) + PADDING
    side = max(content_w, content_h)
    x_off = (side - content_w) // 2  # centre content horizontally

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" '
        f'width="{side * 2}" height="{side * 2}">',
        f'<rect width="{side}" height="{side}" fill="{BG}"/>',
        # title
        f'<text x="{x_off + PADDING}" y="{PADDING + 26}" '
        f'font-family="-apple-system,system-ui,Segoe UI,Helvetica,Arial,sans-serif" '
        f'font-size="22" font-weight="700" fill="{ACCENT}">{_xml_escape(title)}</text>',
        # separator
        f'<line x1="{x_off + PADDING}" y1="{PADDING + TITLE_H - 8}" '
        f'x2="{x_off + content_w - PADDING}" y2="{PADDING + TITLE_H - 8}" '
        f'stroke="{PANEL}" stroke-width="1"/>',
    ]

    for i, (name, label) in enumerate(items):
        col, row = i % COLS, i // COLS
        cx = x_off + PADDING + col * CELL
        cy = PADDING + TITLE_H + row * (CELL + ROW_LABEL_H)
        ix = cx + (CELL - ICON_PX) // 2
        iy = cy + 4
        parts.append(_icon_group(name, ix, iy))
        parts.append(
            f'<text x="{cx + CELL // 2}" y="{cy + ICON_PX + 16}" '
            f'font-family="-apple-system,system-ui,Segoe UI,Helvetica,Arial,sans-serif" '
            f'font-size="10" fill="{LABEL}" opacity="0.85" text-anchor="middle">'
            f'{_xml_escape(label)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _folder_pair_svg(title: str, items: list[tuple[str, str]]) -> str:
    """A grid where each cell shows the closed + open folder pair, square canvas."""
    cell_w = 96
    rows = (len(items) + COLS - 1) // COLS
    content_w = PADDING * 2 + COLS * cell_w
    content_h = PADDING + TITLE_H + rows * (CELL + ROW_LABEL_H) + PADDING
    side = max(content_w, content_h)
    x_off = (side - content_w) // 2

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {side} {side}" '
        f'width="{side * 2}" height="{side * 2}">',
        f'<rect width="{side}" height="{side}" fill="{BG}"/>',
        f'<text x="{x_off + PADDING}" y="{PADDING + 26}" '
        f'font-family="-apple-system,system-ui,Segoe UI,Helvetica,Arial,sans-serif" '
        f'font-size="22" font-weight="700" fill="{ACCENT}">{_xml_escape(title)}</text>',
        f'<line x1="{x_off + PADDING}" y1="{PADDING + TITLE_H - 8}" '
        f'x2="{x_off + content_w - PADDING}" y2="{PADDING + TITLE_H - 8}" '
        f'stroke="{PANEL}" stroke-width="1"/>',
    ]

    size = 36
    for i, (key, label) in enumerate(items):
        col, row = i % COLS, i // COLS
        cx = x_off + PADDING + col * cell_w
        cy = PADDING + TITLE_H + row * (CELL + ROW_LABEL_H)
        parts.append(_icon_group(f"folder_{key}", cx + 6, cy + 6, size))
        parts.append(_icon_group(f"folder_{key}_open", cx + cell_w // 2 + 6, cy + 6, size))
        parts.append(
            f'<text x="{cx + cell_w // 2}" y="{cy + size + 18}" '
            f'font-family="-apple-system,system-ui,Segoe UI,Helvetica,Arial,sans-serif" '
            f'font-size="10" fill="{LABEL}" opacity="0.85" text-anchor="middle">'
            f'{_xml_escape(label)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


# ----- Curated previews ----------------------------------------------------- #
# Note: titles avoid '&' to keep the SVG clean; '&' is escaped anyway, but
# rendered ampersands hurt at-a-glance scanning.
LANGUAGES: list[tuple[str, str]] = [
    ("typescript", "ts"), ("javascript", "js"), ("react", "tsx/jsx"),
    ("vue", "vue"), ("angular", "angular"), ("svelte", "svelte"),
    ("astro", "astro"), ("html", "html"), ("css", "css"),
    ("scss", "scss"), ("sass", "sass"), ("less", "less"),
    ("python", "py"), ("java", "java"), ("kotlin", "kt"),
    ("go", "go"), ("rust", "rs"), ("ruby", "rb"),
    ("swift", "swift"), ("dart", "dart"), ("php", "php"),
    ("csharp", "cs"), ("cpp", "cpp"), ("c", "c"),
    ("scala", "scala"), ("clojure", "clj"), ("perl", "pl"),
    ("lua", "lua"), ("haskell", "hs"), ("elixir", "ex"),
    ("erlang", "erl"), ("julia", "jl"),
]

DATA_OPS: list[tuple[str, str]] = [
    ("json", "json"), ("yaml", "yaml"), ("xml", "xml"), ("toml", "toml"),
    ("env", "env"), ("ini", "ini"),
    ("markdown", "md"), ("mdx", "mdx"), ("text", "txt"), ("log", "log"),
    ("csv", "csv"), ("tex", "tex"),
    ("sql", "sql"), ("graphql", "gql"), ("prisma", "prisma"),
    ("database", "db"), ("shell", "sh"), ("bash", "bash"),
    ("zsh", "zsh"), ("powershell", "ps1"),
    ("docker", "docker"), ("docker_compose", "compose"),
    ("git", "git"), ("gitignore", ".gitignore"),
]

TOOLING: list[tuple[str, str]] = [
    ("npm", "npm"), ("yarn", "yarn"), ("pnpm", "pnpm"), ("bun", "bun"),
    ("eslint", "eslint"), ("prettier", "prettier"),
    ("babel", "babel"), ("editorconfig", "editorconfig"),
    ("vite", "vite"), ("webpack", "webpack"),
    ("rollup", "rollup"), ("parcel", "parcel"),
    ("turbo", "turbo"), ("nx", "nx"),
    ("jest", "jest"), ("vitest", "vitest"),
    ("cypress", "cypress"), ("playwright", "playwright"),
    ("storybook", "storybook"), ("mocha", "mocha"),
    ("makefile", "make"), ("cmake", "cmake"),
    ("gradle", "gradle"), ("cargo", "cargo"),
]

FILES: list[tuple[str, str]] = [
    ("readme", "README"), ("license", "LICENSE"), ("changelog", "CHANGELOG"),
    ("contributing", "CONTRIBUTING"), ("authors", "AUTHORS"), ("settings", "settings"),
    ("certificate", "cert"), ("key", "key"),
    ("image", "image"), ("font", "font"),
    ("archive", "archive"), ("audio", "audio"),
    ("video", "video"), ("pdf", "pdf"),
    ("word", "word"), ("excel", "excel"),
    ("powerpoint", "ppt"), ("notebook", "ipynb"),
    ("disc", "iso"), ("vm", "vm"),
    ("binary", "bin"), ("exe", "exe"),
    ("lock", "lock"), ("svg_icon", "svg"),
]

FOLDERS: list[tuple[str, str]] = [
    ("src", "src"), ("dist", "dist"), ("build", "build"),
    ("public", "public"), ("assets", "assets"), ("images", "images"),
    ("components", "components"), ("pages", "pages"),
    ("hooks", "hooks"), ("utils", "utils"),
    ("services", "services"), ("api", "api"),
    ("controllers", "controllers"), ("models", "models"),
    ("routes", "routes"), ("store", "store"),
    ("types", "types"), ("config", "config"),
    ("tests", "tests"), ("docs", "docs"),
    ("scripts", "scripts"), ("node_modules", "node_modules"),
    ("git", ".git"), ("github", ".github"),
    ("database", "database"), ("migrations", "migrations"),
    ("auth", "auth"), ("secrets", "secrets"),
    ("locales", "i18n"), ("environment", "env"),
    ("themes", "themes"), ("plugins", "plugins"),
]


# ----- Driver --------------------------------------------------------------- #
def _svg_to_png(svg_path: Path, png_path: Path) -> None:
    out_dir = svg_path.parent
    tmp = out_dir / f"{svg_path.name}.png"
    if tmp.exists():
        tmp.unlink()
    subprocess.run(
        ["qlmanage", "-t", "-s", str(THUMB_SIZE), "-o", str(out_dir), str(svg_path)],
        check=True,
        capture_output=True,
    )
    if not tmp.exists():
        raise RuntimeError(f"qlmanage produced no output for {svg_path}")
    if png_path.exists():
        png_path.unlink()
    tmp.rename(png_path)


def _emit(slug: str, title: str, items: list, *, pairs: bool = False) -> Path:
    svg_path = PREVIEWS_DIR / f"{slug}.svg"
    png_path = PREVIEWS_DIR / f"{slug}.png"
    content = (_folder_pair_svg if pairs else _grid_svg)(title, items)
    svg_path.write_text(content, encoding="utf-8")
    _svg_to_png(svg_path, png_path)
    return png_path


def main() -> None:
    if not shutil.which("qlmanage"):
        raise SystemExit("qlmanage not found — this script requires macOS Quick Look.")
    PREVIEWS_DIR.mkdir(exist_ok=True)
    for png in [
        _emit("languages", "Languages",          LANGUAGES),
        _emit("data-ops",  "Data, config, ops",  DATA_OPS),
        _emit("tooling",   "Build and tests",    TOOLING),
        _emit("files",     "Special files",      FILES),
        _emit("folders",   "Folders",            FOLDERS, pairs=True),
    ]:
        print(f"  wrote {png.relative_to(ROOT)}  ({png.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
