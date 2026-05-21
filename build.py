#!/usr/bin/env python3
"""
Build script for the Lusitania Icon Theme.

Generates:
  - icons/*.svg                : all file & folder SVG icons (32x32)
  - lusitania-icons-theme.json : the VS Code icon theme mapping

Design language
---------------
Inspired by IntelliJ *Atom Material Icons* and the VS Code *Material Icon
Theme*, recoloured with the Lusitania deep-sea palette.

  - 32x32 viewBox, flat, no strokes (except where a logo demands it).
  - Each technology has its own *silhouette* — never a generic letter chip
    on a document. Brand-recognisable tech (TypeScript, React, Vue, HTML,
    Python, Docker, Git, …) uses its actual logo shape; document-style
    formats (txt, csv, log, ini …) use a clean folded document with the
    appropriate inner structure (lines for prose, grid for tabular, key=
    value for config, etc.).
  - Folders are a single-piece tab-folder silhouette, single fill colour,
    plus a small white glyph inset that names the folder's role (braces
    for `src`, a check for `test`, a gear for `config`, …).
  - Open folders use the same shape with the body lightened so the visual
    state change is obvious without changing the silhouette.

Run:  python3 build.py
"""
from __future__ import annotations

import json
import os

# --------------------------------------------------------------------------- #
# Lusitania palette
# --------------------------------------------------------------------------- #
PALETTE = {
    "bg":         "#0d1620",
    "bg_dark":    "#0a0d14",
    "bg_alt":     "#15171c",
    "panel":      "#172534",
    "fg":         "#c3cee3",
    "fg_dim":     "#546e7a",
    "teal":       "#009688",
    "teal_dark":  "#00796b",
    "cyan":       "#80deea",
    "cyan_alt":   "#89ddff",
    "blue":       "#82aaff",
    "purple":     "#c792ea",
    "green":      "#c3e88d",
    "yellow":     "#ffcb6b",
    "orange":     "#f78c6c",
    "red":        "#ff5370",
    "coral":      "#f07178",
    "white":      "#eeffff",
}
C = PALETTE


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def svg(body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        + body
        + "</svg>"
    )


def _shade(hex_color: str, factor: float) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    def adj(v: int) -> int:
        if factor >= 0:
            return int(v + (255 - v) * factor)
        return int(v * (1 + factor))
    return f"#{adj(r):02x}{adj(g):02x}{adj(b):02x}"


# --------------------------------------------------------------------------- #
# Reusable document silhouettes (generic file shapes — no letter badges)
# --------------------------------------------------------------------------- #
def doc_blank(body: str, fold: str | None = None) -> str:
    """Just a folded document — used as a base for inner glyphs."""
    fold = fold or _shade(body, -0.25)
    return (
        f'<path fill="{body}" d="M6 2h13l7 7v21H6z"/>'
        f'<path fill="{fold}" d="M19 2v7h7z"/>'
    )


def doc_lines(body: str, line: str = None, n_lines: int = 4) -> str:
    """Document with horizontal text lines — for txt, log, plaintext."""
    line = line or _shade(body, 0.35)
    rows = [(9, 14), (9, 18), (9, 22), (9, 26)][:n_lines]
    inner = "".join(
        f'<rect x="{x}" y="{y}" width="{[14,12,10,8][i]}" height="1.6" rx="0.8" fill="{line}" opacity="0.7"/>'
        for i, (x, y) in enumerate(rows)
    )
    return svg(doc_blank(body) + inner)


def doc_table(body: str, line: str = None) -> str:
    """Document with a 3x3 grid — for csv, tsv, tabular data."""
    line = line or _shade(body, 0.35)
    grid = (
        f'<g stroke="{line}" stroke-width="1.2" opacity="0.85">'
        '<line x1="9"  y1="14" x2="23" y2="14"/>'
        '<line x1="9"  y1="20" x2="23" y2="20"/>'
        '<line x1="9"  y1="26" x2="23" y2="26"/>'
        '<line x1="14" y1="12" x2="14" y2="28"/>'
        '<line x1="19" y1="12" x2="19" y2="28"/>'
        '</g>'
    )
    return svg(doc_blank(body) + grid)


def doc_config(body: str, line: str = None) -> str:
    """Document with key=value rows — for ini, conf, properties, env."""
    line = line or _shade(body, 0.35)
    inner = (
        f'<g fill="{line}" opacity="0.85">'
        '<rect x="9"  y="14.2" width="4" height="1.6" rx="0.6"/>'
        '<rect x="14" y="14.2" width="1.6" height="1.6" rx="0.6"/>'
        '<rect x="16.5" y="14.2" width="6" height="1.6" rx="0.6"/>'
        '<rect x="9"  y="18.2" width="3" height="1.6" rx="0.6"/>'
        '<rect x="13" y="18.2" width="1.6" height="1.6" rx="0.6"/>'
        '<rect x="15.5" y="18.2" width="7" height="1.6" rx="0.6"/>'
        '<rect x="9"  y="22.2" width="5" height="1.6" rx="0.6"/>'
        '<rect x="15" y="22.2" width="1.6" height="1.6" rx="0.6"/>'
        '<rect x="17.5" y="22.2" width="5" height="1.6" rx="0.6"/>'
        '</g>'
    )
    return svg(doc_blank(body) + inner)


def doc_code(body: str, line: str = None) -> str:
    """Document with indented code-like rows — for unknown source files."""
    line = line or _shade(body, 0.35)
    inner = (
        f'<g fill="{line}" opacity="0.85">'
        '<rect x="9" y="14" width="10" height="1.6" rx="0.8"/>'
        '<rect x="12" y="17.5" width="9" height="1.6" rx="0.8"/>'
        '<rect x="12" y="21" width="7" height="1.6" rx="0.8"/>'
        '<rect x="9" y="24.5" width="11" height="1.6" rx="0.8"/>'
        '</g>'
    )
    return svg(doc_blank(body) + inner)


# --------------------------------------------------------------------------- #
# Folder silhouettes (Atom Material style: single fill, optional inset glyph)
# --------------------------------------------------------------------------- #
def _folder_path(main: str) -> str:
    """Single-piece folder tab silhouette."""
    return (
        f'<path fill="{main}" d="M3 8a2 2 0 0 1 2-2h7l2.5 2.5H27a2 2 0 0 1 2 '
        '2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8z"/>'
    )


def folder_closed(main: str, glyph: str = "") -> str:
    return svg(_folder_path(main) + glyph)


def folder_open(main: str, glyph: str = "") -> str:
    light = _shade(main, 0.30)
    # Same outline; lighten the lower section so it reads as "open".
    return svg(
        _folder_path(main)
        + f'<path fill="{light}" d="M3 14h26v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V14z"/>'
        + glyph
    )


def _glyph_braces() -> str:
    return (
        '<path fill="#fff" opacity="0.95" stroke="#fff" stroke-width="0.4" d="'
        'M13.5 17c-1 0-1.5.5-1.5 1.4v1.2c0 .6-.3.9-.9.9v.8c.6 0 .9.3.9.9v1.2c0 .9.5 1.4 1.5 1.4v-.9c-.5 0-.7-.2-.7-.7v-1.1c0-.6-.2-1-.7-1.2.5-.2.7-.6.7-1.2v-1.1c0-.5.2-.7.7-.7V17z'
        ' M18.5 17v.9c.5 0 .7.2.7.7v1.1c0 .6.2 1 .7 1.2-.5.2-.7.6-.7 1.2v1.1c0 .5-.2.7-.7.7v.9c1 0 1.5-.5 1.5-1.4v-1.2c0-.6.3-.9.9-.9v-.8c-.6 0-.9-.3-.9-.9v-1.2c0-.9-.5-1.4-1.5-1.4z"/>'
    )


def _glyph_check() -> str:
    return (
        '<path fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" '
        'stroke-linejoin="round" d="M11.5 21l3 3 6-6.5"/>'
    )


def _glyph_gear() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<circle cx="16" cy="20.5" r="2.4"/>'
        '<path d="M16 14.2v1.6m0 9.4v1.6m-4.5-6.3h-1.5m12 0h-1.5m-7.4-3.2l-1.1-1.1m9.5 9.5l-1.1-1.1m-7.3 0l-1.1 1.1m9.5-9.5l-1.1 1.1" stroke="#fff" stroke-width="1.4" stroke-linecap="round"/>'
        '</g>'
    )


def _glyph_circle_dot() -> str:
    return '<circle cx="16" cy="20.5" r="2.6" fill="#fff" opacity="0.95"/>'


def _glyph_cube() -> str:
    return (
        '<g fill="none" stroke="#fff" stroke-width="1.6" stroke-linejoin="round" opacity="0.95">'
        '<path d="M16 15l5 2.8v5.6L16 26l-5-2.6v-5.6z"/>'
        '<path d="M16 15v5l5 2.8M16 20l-5-2.8M16 20v6"/>'
        '</g>'
    )


def _glyph_page() -> str:
    return (
        '<path fill="#fff" opacity="0.95" d="M13 15.5h4.5l2 2v6.5h-6.5z M17.5 15.5v2h2"/>'
    )


def _glyph_hook() -> str:
    return (
        '<path fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" '
        'd="M13 16v4a3 3 0 0 0 6 0v-3"/>'
    )


def _glyph_wrench() -> str:
    return (
        '<path fill="#fff" opacity="0.95" d="M21.5 16.2a3.2 3.2 0 0 0-4 4l-5 5 1.4 1.4 5-5a3.2 3.2 0 0 0 4-4l-2 2-1.6-1.6 2-2z"/>'
    )


def _glyph_arrows() -> str:
    return (
        '<g fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M11 18.5h8M17 16.5l2 2-2 2"/>'
        '<path d="M21 23.5h-8M15 25.5l-2-2 2-2"/>'
        '</g>'
    )


def _glyph_route() -> str:
    return (
        '<g fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round">'
        '<circle cx="13" cy="17.5" r="1.6" fill="#fff"/>'
        '<circle cx="19" cy="24"   r="1.6" fill="#fff"/>'
        '<path d="M13 19v1.5a2 2 0 0 0 2 2h2a2 2 0 0 1 2 2"/>'
        '</g>'
    )


def _glyph_box() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<path d="M12 16h8l1 2v6h-10v-6z" fill-opacity="0"/>'
        '<path d="M12 16l-1 2h10l-1-2zM11 18h10v6H11zm4 1.5v3" stroke="#fff" stroke-width="1.2" fill="none"/>'
        '</g>'
    )


def _glyph_globe() -> str:
    return (
        '<g fill="none" stroke="#fff" stroke-width="1.4">'
        '<circle cx="16" cy="20.5" r="4"/>'
        '<ellipse cx="16" cy="20.5" rx="2" ry="4"/>'
        '<line x1="12" y1="20.5" x2="20" y2="20.5"/>'
        '</g>'
    )


def _glyph_lock() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<path d="M13 19v-1.5a3 3 0 0 1 6 0V19" fill="none" stroke="#fff" stroke-width="1.6"/>'
        '<rect x="12" y="19" width="8" height="6" rx="1"/>'
        '</g>'
    )


def _glyph_book() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<path d="M11 16h4a2 2 0 0 1 2 2v8a2 2 0 0 0-2-2h-4z"/>'
        '<path d="M21 16h-4a2 2 0 0 0-2 2v8a2 2 0 0 1 2-2h4z" opacity="0.75"/>'
        '</g>'
    )


def _glyph_image() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<rect x="11" y="15.5" width="10" height="8" rx="1"/>'
        '<circle cx="13.5" cy="18" r="0.9" fill="#0d1620"/>'
        '<path d="M11 22l3-3 2 2 2-2 3 3v1.5h-10z" fill="#0d1620"/>'
        '</g>'
    )


def _glyph_terminal() -> str:
    return (
        '<g fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M11 16l3 3-3 3"/>'
        '<line x1="16" y1="23.5" x2="21" y2="23.5"/>'
        '</g>'
    )


def _glyph_branch() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<circle cx="13" cy="16.5" r="1.5"/>'
        '<circle cx="13" cy="24" r="1.5"/>'
        '<circle cx="20" cy="20" r="1.5"/>'
        '<path d="M13 18v4M13 20q0 2 3.5 2t3.5-2" fill="none" stroke="#fff" stroke-width="1.4"/>'
        '</g>'
    )


def _glyph_at() -> str:
    return (
        '<text x="16" y="24.5" font-family="-apple-system, system-ui, sans-serif" '
        'font-size="10" font-weight="700" text-anchor="middle" fill="#fff">@</text>'
    )


def _glyph_dl() -> str:
    return (
        '<g fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M16 14v8"/><path d="M12 20l4 4 4-4"/>'
        '</g>'
    )


def _glyph_ul() -> str:
    return (
        '<g fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M16 24v-8"/><path d="M12 18l4-4 4 4"/>'
        '</g>'
    )


def _glyph_db() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<ellipse cx="16" cy="16.5" rx="4.5" ry="1.4"/>'
        '<path d="M11.5 16.5v6c0 .8 2 1.4 4.5 1.4s4.5-.6 4.5-1.4v-6"/>'
        '<path d="M11.5 19.5c0 .8 2 1.4 4.5 1.4s4.5-.6 4.5-1.4" stroke="#0d1620" stroke-width="0.7" fill="none"/>'
        '</g>'
    )


def _glyph_info() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<circle cx="16" cy="20.5" r="4"/>'
        '<text x="16" y="23" font-family="Georgia, serif" font-size="6" font-style="italic" font-weight="800" text-anchor="middle" fill="#0d1620">i</text>'
        '</g>'
    )


def _glyph_test_tube() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<path d="M14 14h4v6l2 4a2 2 0 0 1-2 2.5h-4a2 2 0 0 1-2-2.5l2-4v-6z" fill="none" stroke="#fff" stroke-width="1.4"/>'
        '<path d="M13 21h6" stroke="#fff" stroke-width="1.4"/>'
        '</g>'
    )


def _glyph_v_blue() -> str:
    return (
        '<path fill="#fff" opacity="0.95" d="M11 15l5 9 5-9h-2.5L16 20.5 13.5 15z"/>'
    )


def _glyph_chart() -> str:
    return (
        '<g fill="#fff" opacity="0.95">'
        '<rect x="11" y="22" width="2.5" height="3.5"/>'
        '<rect x="14.5" y="19" width="2.5" height="6.5"/>'
        '<rect x="18" y="16" width="2.5" height="9.5"/>'
        '</g>'
    )


def _glyph_atom() -> str:
    return (
        '<g fill="none" stroke="#fff" stroke-width="1.2">'
        '<circle cx="16" cy="20.5" r="1.4" fill="#fff"/>'
        '<ellipse cx="16" cy="20.5" rx="5.5" ry="2"/>'
        '<ellipse cx="16" cy="20.5" rx="5.5" ry="2" transform="rotate(60 16 20.5)"/>'
        '<ellipse cx="16" cy="20.5" rx="5.5" ry="2" transform="rotate(120 16 20.5)"/>'
        '</g>'
    )


# --------------------------------------------------------------------------- #
# Language / tool icons (each one a unique silhouette)
# --------------------------------------------------------------------------- #
def _lang_chip(letters: str, bg: str, fg: str = None, size: int = 11) -> str:
    """Rounded square with bold letters — used only for langs that brand
    themselves this way: TypeScript, JavaScript, C, C++, C#, Go, R."""
    fg = fg or C["bg"]
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{bg}"/>'
        f'<text x="16" y="22" font-family="-apple-system, system-ui, sans-serif" '
        f'font-size="{size}" font-weight="800" letter-spacing="-0.5" text-anchor="middle" fill="{fg}">{letters}</text>'
    )


def i_typescript():
    return _lang_chip("TS", C["blue"])


def i_typescript_def():
    # .d.ts gets a slightly different visual to differentiate
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{C["purple"]}"/>'
        f'<text x="16" y="22" font-family="-apple-system, system-ui, sans-serif" '
        f'font-size="9" font-weight="800" letter-spacing="-0.5" text-anchor="middle" fill="{C["bg"]}">.d.ts</text>'
    )


def i_javascript():
    return _lang_chip("JS", C["yellow"])


def i_react():
    c = C["cyan"]
    return svg(
        f'<circle cx="16" cy="16" r="2.6" fill="{c}"/>'
        f'<g fill="none" stroke="{c}" stroke-width="1.6">'
        '<ellipse cx="16" cy="16" rx="11" ry="4.2"/>'
        '<ellipse cx="16" cy="16" rx="11" ry="4.2" transform="rotate(60 16 16)"/>'
        '<ellipse cx="16" cy="16" rx="11" ry="4.2" transform="rotate(120 16 16)"/>'
        '</g>'
    )


def i_vue():
    g, d = C["green"], _shade(C["green"], -0.35)
    return svg(
        f'<path fill="{g}" d="M2 6h6l8 13L24 6h6L16 28z"/>'
        f'<path fill="{d}" d="M8 6h5l3 5 3-5h5L16 19z"/>'
    )


def i_angular():
    r = C["red"]
    return svg(
        f'<path fill="{r}" d="M16 2L3 6.5l2 18 11 5.5 11-5.5 2-18z"/>'
        f'<path fill="{_shade(r, -0.18)}" d="M16 4.2v23.8l9-4.5 1.6-15z"/>'
        f'<path fill="#fff" d="M16 8l-5.5 12.5h2.3l1.2-3h4l1.2 3h2.3L16 8zm-1.4 7.6L16 12l1.4 3.6z"/>'
    )


def i_svelte():
    o = C["orange"]
    return svg(
        f'<path fill="{o}" d="M24.6 5.2c-3.3-2.4-7.9-1.7-10.3 1.7L9.5 13c-1.5 2-1.7 4.7-.6 7-1.7 2.5-1.4 5.9.9 8 3.3 2.4 7.9 1.7 10.3-1.7l4.8-6.1c1.5-2 1.7-4.7.6-7 1.7-2.5 1.4-5.9-.9-8z"/>'
        f'<path fill="{C["bg"]}" d="M14.6 25.4c-1.6-.4-2.4-2.2-1.6-3.7l.2-.3.2-.2 4.2 3-.7.5c-.7.5-1.6.7-2.3.7zm6.2-12.1c.6-1.1 2-1.4 3-.6 1.1.7 1.4 2.2.7 3.2l-.2.3-.2.2-4.2-3z"/>'
    )


def i_astro():
    o = C["orange"]
    return svg(
        f'<path fill="{o}" d="M11 26l5-21 5 21-5-3-5 3z"/>'
        f'<path fill="{_shade(o, 0.25)}" d="M16 5v18l-5 3 5-3 5 3z" opacity="0.6"/>'
    )


def i_html():
    c = C["coral"]
    return svg(
        f'<path fill="{c}" d="M5 3l2.2 25.3L16 30l8.8-1.7L27 3z"/>'
        f'<path fill="{_shade(c, -0.2)}" d="M16 5.5v22.6l7.1-1.4 1.9-21.2z"/>'
        f'<path fill="#fff" d="M11.4 11h9.2l-.3 2.6H14l.2 2.4h6l-.3 2.6h-5.5l.3 2.7 3.6 1 3.6-1 .3-3h2.6l-.6 5L16 24.4 8.7 22l-.5-6h2.6l.3 3 2.4.7-.2-2.4-2.7-.1z"/>'
    )


def i_css():
    b = C["blue"]
    return svg(
        f'<path fill="{b}" d="M5 3l2.2 25.3L16 30l8.8-1.7L27 3z"/>'
        f'<path fill="{_shade(b, -0.25)}" d="M16 5.5v22.6l7.1-1.4 1.9-21.2z"/>'
        f'<path fill="#fff" d="M11.4 13.6l-.2-2.6h13.5l-.5 5.4-7.3 2.4v.2l-.7 2.6 2.4-.6 3.6-1-.2 2.4-3.6 1-3.6-1-.4-3h2.6l.2 1.4 1.4-.1.2-2.4-6.3-.1.3 2.6h5.5l.2 2.4H12.2l-.3-2.5h2.4l-.1-1.7z"/>'
    )


def i_scss():
    r = C["red"]
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{r}"/>'
        f'<path fill="#fff" d="M10 14c0-2 2.5-3.5 6-3.5s6 1.5 6 3.5-2.5 3.5-6 3.5c-1.4 0-2.7-.2-3.7-.6.4 1.3 2 2.6 4.7 2.6 2 0 3.4-.7 4.5-1.6l1 1.4c-1.5 1.2-3.3 2-5.5 2-4 0-6.5-2.4-6.5-5 0-2 1.9-3.3 4.3-3.9-3.5.2-5.8 1.5-5.8 3.1z"/>'
    )


def i_sass():
    # softer pink-ish for distinguishing from scss
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{C["coral"]}"/>'
        f'<path fill="#fff" d="M10 14c0-2 2.5-3.5 6-3.5s6 1.5 6 3.5-2.5 3.5-6 3.5c-1.4 0-2.7-.2-3.7-.6.4 1.3 2 2.6 4.7 2.6 2 0 3.4-.7 4.5-1.6l1 1.4c-1.5 1.2-3.3 2-5.5 2-4 0-6.5-2.4-6.5-5 0-2 1.9-3.3 4.3-3.9-3.5.2-5.8 1.5-5.8 3.1z"/>'
    )


def i_less():
    return _lang_chip("Less", C["blue"], size=9)


def i_stylus():
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{C["green"]}"/>'
        f'<text x="16" y="22" font-family="Georgia, serif" font-size="14" font-style="italic" font-weight="800" text-anchor="middle" fill="{C["bg"]}">s</text>'
    )


def i_python():
    b, y = C["blue"], C["yellow"]
    return svg(
        # Top snake (blue)
        f'<path fill="{b}" d="M15.9 2c-3.1 0-4 1.4-4 3v3.5h4.2v.6H8.7c-2.2 0-3.7 1.4-3.7 4.9 0 3.4 1.4 4.9 3.7 4.9h2v-3c0-1.9 1.5-3.4 3.4-3.4h6.7c1.6 0 3-1.3 3-3V5c0-1.7-1.5-3-3.5-3-1.5 0-3-.3-4.4 0zm-1.6 2.4c.6 0 1.1.5 1.1 1.2s-.5 1.2-1.1 1.2-1.1-.5-1.1-1.2.5-1.2 1.1-1.2z"/>'
        # Bottom snake (yellow)
        f'<path fill="{y}" d="M16.1 30c3.1 0 4-1.4 4-3v-3.5h-4.2v-.6h7.4c2.2 0 3.7-1.4 3.7-4.9 0-3.4-1.4-4.9-3.7-4.9h-2v3c0 1.9-1.5 3.4-3.4 3.4h-6.7c-1.6 0-3 1.3-3 3V27c0 1.7 1.5 3 3.5 3 1.5 0 3 .3 4.4 0zm1.6-2.4c-.6 0-1.1-.5-1.1-1.2s.5-1.2 1.1-1.2 1.1.5 1.1 1.2-.5 1.2-1.1 1.2z"/>'
    )


def i_java():
    o, r = C["orange"], C["red"]
    return svg(
        # cup
        f'<path fill="{o}" d="M7 19h17v3.5c0 2-3 3.5-8.5 3.5s-8.5-1.5-8.5-3.5V19z"/>'
        f'<path fill="{_shade(o, -0.2)}" d="M7 19h17v1.5c0 1.2-3 2-8.5 2s-8.5-.8-8.5-2V19z"/>'
        # handle
        f'<path fill="none" stroke="{o}" stroke-width="1.6" d="M24 19.5c2 0 3 1 3 2.5s-1 2-3 2.5"/>'
        # steam
        f'<g fill="{r}">'
        '<path d="M14 3c0 2.5-2 3-2 5s1.5 3 1.5 5c0 1.5-1 2-1 3"/>'
        '<path d="M18 5c0 2-1.5 2.5-1.5 4s1 2.5 1 4.5"/>'
        '</g>'
        f'<g fill="none" stroke="{r}" stroke-width="1.6" stroke-linecap="round">'
        '<path d="M14 3c0 2.5-2 3-2 5s1.5 3 1.5 5c0 1.5-1 2-1 3"/>'
        '<path d="M18 5c0 2-1.5 2.5-1.5 4s1 2.5 1 4.5"/>'
        '</g>'
    )


def i_class():
    # compiled java class
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{C["orange"]}"/>'
        f'<text x="16" y="22" font-family="-apple-system, system-ui, sans-serif" '
        f'font-size="14" font-weight="800" text-anchor="middle" fill="{C["bg"]}">C</text>'
    )


def i_jar():
    o = C["orange"]
    return svg(
        f'<path fill="{o}" d="M9 4h14v3h-14zM7 8h18v22H7z"/>'
        f'<rect x="7" y="13" width="18" height="3" fill="{_shade(o, -0.2)}"/>'
        f'<rect x="13" y="16" width="6" height="6" fill="{C["bg"]}"/>'
    )


def i_kotlin():
    return svg(
        '<defs><linearGradient id="kt" x1="0" y1="1" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{C["purple"]}"/>'
        f'<stop offset="0.5" stop-color="{C["coral"]}"/>'
        f'<stop offset="1" stop-color="{C["orange"]}"/>'
        '</linearGradient></defs>'
        '<path fill="url(#kt)" d="M3 3h26v26L16 16 3 29z"/>'
    )


def i_groovy():
    return svg(
        f'<path fill="{C["cyan_alt"]}" d="M5 6h22c0 4-4 6-8 6-2 0-4-.5-6-.5-3 0-5 1.5-5 4.5h-3V6z"/>'
        f'<path fill="{_shade(C["cyan_alt"], -0.2)}" d="M5 16h3c0 4 3 6 7 6h12v4H5z"/>'
    )


def i_scala():
    r = C["red"]
    return svg(
        f'<g fill="{r}">'
        '<path d="M6 4h20v5L6 11z"/>'
        '<path d="M6 12h20v5L6 19z"/>'
        '<path d="M6 20h20v5L6 27z"/>'
        '</g>'
    )


def i_clojure():
    g = C["green"]
    return svg(
        f'<circle cx="16" cy="16" r="13" fill="none" stroke="{g}" stroke-width="3"/>'
        f'<circle cx="13" cy="13" r="2.8" fill="{C["blue"]}"/>'
        f'<circle cx="19" cy="13" r="2.8" fill="{g}"/>'
        f'<circle cx="16" cy="20" r="2.8" fill="{_shade(g, -0.2)}"/>'
    )


def i_go():
    cy = C["cyan_alt"]
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{cy}"/>'
        f'<text x="16" y="22" font-family="-apple-system, system-ui, sans-serif" '
        f'font-size="13" font-style="italic" font-weight="800" text-anchor="middle" fill="{C["bg"]}">Go</text>'
    )


def i_rust():
    o = C["orange"]
    return svg(
        # gear-like ring
        f'<g fill="{o}">'
        '<circle cx="16" cy="16" r="9"/>'
        '<path d="M16 2l2 4-2 1-2-1zM16 30l-2-4 2-1 2 1zM2 16l4-2 1 2-1 2zM30 16l-4 2-1-2 1-2zM6 6l4 1-1 3-3-1zM26 26l-4-1 1-3 3 1zM6 26l1-4 3 1-1 3zM26 6l-1 4-3-1 1-3z"/>'
        '</g>'
        # center R
        f'<circle cx="16" cy="16" r="6.5" fill="{C["bg"]}"/>'
        f'<text x="16" y="20.5" font-family="-apple-system, system-ui, sans-serif" '
        f'font-size="10" font-weight="900" text-anchor="middle" fill="{o}">R</text>'
    )


def i_ruby():
    r = C["red"]
    return svg(
        # gem cut
        f'<path fill="{r}" d="M16 3l13 8-3.5 18-9.5 1-9.5-1L3 11z"/>'
        f'<path fill="{_shade(r, 0.3)}" d="M16 3l-5 8h10z" opacity="0.7"/>'
        f'<path fill="{_shade(r, -0.25)}" d="M3 11l8 4 5-12-8 8z" opacity="0.5"/>'
        f'<path fill="{_shade(r, -0.25)}" d="M29 11l-8 4-5-12 8 8z" opacity="0.5"/>'
        f'<path fill="none" stroke="{_shade(r, -0.35)}" stroke-width="0.7" d="M11 11l5 18 5-18z"/>'
    )


def i_swift():
    o = C["orange"]
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="6" fill="{o}"/>'
        f'<path fill="#fff" d="M22 24c-3 2-7 1.2-10 -1 1.5.5 3.5.6 5.5-.3-3-1.8-5.4-4.4-7-7 .5 0 1.5.4 3 1-2-2.4-3-5.4-3-5.4 2.4 2.4 5.6 4 5.6 4-1.7-2.4-2.5-5-2.5-5C16 13.4 21 16 21 16c.2-.6.3-1.2.4-2 1 1.6 1.6 3.4 1.6 5 1 1 1.5 2.3 0 5z"/>'
    )


def i_dart():
    b = C["blue"]
    return svg(
        f'<path fill="{b}" d="M5 16L16 5l11 11-11 11z"/>'
        f'<path fill="{C["cyan"]}" d="M16 5v22l11-11z" opacity="0.75"/>'
        f'<path fill="#fff" d="M16 11l5 5-5 5z"/>'
    )


def i_php():
    p = C["purple"]
    return svg(
        f'<ellipse cx="16" cy="16" rx="13" ry="8" fill="{p}"/>'
        f'<ellipse cx="16" cy="16" rx="13" ry="8" fill="none" stroke="{_shade(p, -0.3)}" stroke-width="0.8"/>'
        f'<text x="16" y="19" font-family="-apple-system, system-ui, sans-serif" '
        f'font-size="9" font-weight="800" font-style="italic" text-anchor="middle" fill="{C["bg"]}">php</text>'
    )


def i_csharp():
    return _lang_chip("C#", C["purple"], size=13)


def i_cpp():
    return _lang_chip("C++", C["blue"], size=11)


def i_c():
    return _lang_chip("C", C["blue"], size=15)


def i_header():
    return _lang_chip("h", C["purple"], size=15)


def i_objective_c():
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{C["blue"]}"/>'
        f'<text x="16" y="22" font-family="-apple-system, system-ui, sans-serif" '
        f'font-size="13" font-weight="800" text-anchor="middle" fill="{C["bg"]}">obj</text>'
    )


def i_perl():
    cy = C["cyan_alt"]
    return svg(
        # onion-ish bulb
        f'<path fill="{cy}" d="M16 4c-4 0-6 3-6 6 0 3 2 4 2 7s-2 4-2 7c0 2 2 4 6 4s6-2 6-4c0-3-2-4-2-7s2-4 2-7c0-3-2-6-6-6z"/>'
        f'<circle cx="16" cy="9.5" r="2" fill="#fff" opacity="0.7"/>'
    )


def i_lua():
    p = C["purple"]
    return svg(
        # moon
        f'<circle cx="16" cy="16" r="11" fill="{p}"/>'
        f'<circle cx="19" cy="14" r="9" fill="{C["bg"]}"/>'
    )


def i_haskell():
    p = C["purple"]
    return svg(
        # stylised lambda
        f'<g fill="{p}">'
        '<path d="M5 5l5 9-5 13h4l5-13L9 5z"/>'
        '<path d="M13 5l9 22h4L17 5z"/>'
        '<path d="M14 15h13v3H14z"/>'
        '<path d="M19 21h8v3h-8z"/>'
        '</g>'
    )


def i_elixir():
    p = C["purple"]
    return svg(
        # drop
        f'<path fill="{p}" d="M16 3c-3 6-9 11-9 18 0 5 4 8 9 8s9-3 9-8c0-7-6-12-9-18z"/>'
        f'<path fill="#fff" d="M11 18c-1 3 0 6 2 7" opacity="0.5"/>'
    )


def i_erlang():
    r = C["red"]
    return svg(
        f'<rect x="3" y="3" width="26" height="26" rx="3" fill="{r}"/>'
        f'<path fill="#fff" d="M8 9h6c2 0 4 1 4 4s-2 4-4 4h-3v6H8V9zm3 3v2.5h2.5c.6 0 1-.4 1-1.2s-.4-1.2-1-1.2H11z"/>'
        f'<path fill="#fff" d="M19 17l5 6h-4l-3-4z"/>'
    )


def i_r_lang():
    return _lang_chip("R", C["cyan_alt"], size=14)


def i_julia():
    return svg(
        f'<g>'
        f'<circle cx="9"  cy="11" r="4" fill="{C["purple"]}"/>'
        f'<circle cx="23" cy="11" r="4" fill="{C["green"]}"/>'
        f'<circle cx="16" cy="22" r="4" fill="{C["red"]}"/>'
        f'</g>'
    )


def i_zig():
    o = C["orange"]
    return svg(
        f'<path fill="{o}" d="M5 5h22l-6 8h6L5 27h22l-6-8h-6L21 8H5z"/>'
    )


# --------------------------------------------------------------------------- #
# Data / markup / config
# --------------------------------------------------------------------------- #
def i_json():
    y = C["yellow"]
    return svg(
        doc_blank(y)
        + '<g fill="none" stroke="#0d1620" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 14c-2 0-2 1.5-2 3v1c0 1-.5 1.5-1.5 1.5 1 0 1.5.5 1.5 1.5v1c0 1.5 0 3 2 3"/>'
        '<path d="M18 14c2 0 2 1.5 2 3v1c0 1 .5 1.5 1.5 1.5-1 0-1.5.5-1.5 1.5v1c0 1.5 0 3-2 3"/>'
        '</g>'
    )


def i_yaml():
    r = C["red"]
    return svg(
        doc_blank(r)
        + '<g fill="none" stroke="#fff" stroke-width="1.4" stroke-linecap="round">'
        '<circle cx="10" cy="15" r="1.2" fill="#fff"/><line x1="13" y1="15" x2="22" y2="15"/>'
        '<circle cx="12" cy="19" r="1.2" fill="#fff"/><line x1="15" y1="19" x2="22" y2="19"/>'
        '<circle cx="10" cy="23" r="1.2" fill="#fff"/><line x1="13" y1="23" x2="22" y2="23"/>'
        '</g>'
    )


def i_xml():
    o = C["orange"]
    return svg(
        doc_blank(o)
        + '<g fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M13 17l-2 2 2 2"/><path d="M19 17l2 2-2 2"/><path d="M17 16l-2 8"/>'
        '</g>'
    )


def i_toml():
    o = C["orange"]
    return doc_config(o)


def i_ini():
    return doc_config(C["fg_dim"])


def i_conf():
    return doc_config(C["fg_dim"])


def i_env():
    y = C["yellow"]
    return svg(
        f'<rect x="2" y="5" width="28" height="22" rx="3" fill="{y}"/>'
        '<g fill="#0d1620" font-family="-apple-system, system-ui, sans-serif" font-size="4.5" font-weight="800">'
        '<text x="5" y="13">KEY=</text>'
        '<text x="5" y="20">●●●●●</text>'
        '<text x="5" y="26">URL=</text>'
        '</g>'
    )


def i_markdown():
    cy = C["cyan_alt"]
    return svg(
        f'<rect x="2" y="6" width="28" height="20" rx="3" fill="{C["panel"]}" stroke="{cy}" stroke-width="1.6"/>'
        f'<path fill="{cy}" d="M6 22V11h2l3 4 3-4h2v11h-2v-7l-3 4-3-4v7zM22 17V11h2v6h2l-3 4-3-4z"/>'
    )


def i_mdx():
    cy = C["cyan_alt"]
    return svg(
        f'<rect x="2" y="6" width="28" height="20" rx="3" fill="{C["panel"]}" stroke="{cy}" stroke-width="1.6"/>'
        f'<path fill="{cy}" d="M5 22V11h2l3 4 3-4h2v11h-2v-7l-3 4-3-4v7z"/>'
        f'<path fill="{C["purple"]}" d="M19 11l4 5.5L19 22h2l3-4.2L27 22h2l-4-5.5L29 11h-2l-3 4.2L21 11z"/>'
    )


def i_rst():
    return doc_lines(C["cyan_alt"])


def i_text():
    return doc_lines(C["fg_dim"])


def i_log():
    return doc_lines(C["fg_dim"], n_lines=4)


def i_csv():
    return doc_table(C["green"])


def i_tsv():
    return doc_table(C["green"])


def i_tex():
    r = C["red"]
    return svg(
        doc_blank(r)
        + '<text x="16" y="24" font-family="Times, serif" font-size="11" font-weight="800" '
        'font-style="italic" text-anchor="middle" fill="#fff">TeX</text>'
    )


# --------------------------------------------------------------------------- #
# Shells / db / docker / vcs
# --------------------------------------------------------------------------- #
def _terminal(letters: str, accent: str) -> str:
    return svg(
        f'<rect x="2" y="4" width="28" height="24" rx="3" fill="{C["panel"]}"/>'
        f'<rect x="2" y="4" width="28" height="5" rx="3" fill="{accent}"/>'
        f'<rect x="2" y="6" width="28" height="3" fill="{accent}"/>'
        f'<circle cx="5.5" cy="6.5" r="1" fill="{C["bg"]}"/>'
        f'<circle cx="8.5" cy="6.5" r="1" fill="{C["bg"]}"/>'
        f'<circle cx="11.5" cy="6.5" r="1" fill="{C["bg"]}"/>'
        f'<g fill="none" stroke="{accent}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M7 15l3 3-3 3"/><line x1="13" y1="22" x2="20" y2="22"/>'
        '</g>'
    )


def i_shell():
    return _terminal("$", C["green"])


def i_bash():
    return _terminal("bash", C["green"])


def i_zsh():
    return _terminal("zsh", C["green"])


def i_fish():
    return _terminal("fish", C["cyan"])


def i_powershell():
    return _terminal("ps", C["blue"])


def i_batch():
    return _terminal("bat", C["fg_dim"])


def i_docker():
    b, c = C["blue"], C["cyan_alt"]
    return svg(
        # container stack
        f'<g fill="{b}">'
        '<rect x="6"  y="13" width="3.6" height="3.6" rx="0.5"/>'
        '<rect x="10" y="13" width="3.6" height="3.6" rx="0.5"/>'
        '<rect x="14" y="13" width="3.6" height="3.6" rx="0.5"/>'
        '<rect x="18" y="13" width="3.6" height="3.6" rx="0.5"/>'
        '<rect x="10" y="9"  width="3.6" height="3.6" rx="0.5"/>'
        '<rect x="14" y="9"  width="3.6" height="3.6" rx="0.5"/>'
        '<rect x="14" y="5"  width="3.6" height="3.6" rx="0.5"/>'
        '</g>'
        # whale body
        f'<path fill="{c}" d="M26 17h-2c-.5 2.5-2.5 5-7 5H6c-1 4 1 6 5 6h11c4 0 7-2 9-5h3v-3c0-2-3-3-8-3z"/>'
    )


def i_docker_compose():
    # stacked compose: 3 horizontal containers
    return svg(
        f'<g fill="{C["blue"]}">'
        '<rect x="4" y="8"  width="24" height="5" rx="1.2"/>'
        '<rect x="4" y="14" width="24" height="5" rx="1.2"/>'
        '<rect x="4" y="20" width="24" height="5" rx="1.2"/>'
        '</g>'
        f'<g fill="{C["cyan_alt"]}">'
        '<circle cx="7.5" cy="10.5" r="0.8"/>'
        '<circle cx="7.5" cy="16.5" r="0.8"/>'
        '<circle cx="7.5" cy="22.5" r="0.8"/>'
        '</g>'
    )


def i_sql():
    t = C["teal"]
    d = _shade(t, -0.25)
    return svg(
        f'<ellipse cx="16" cy="7" rx="11" ry="4" fill="{t}"/>'
        f'<path fill="{t}" d="M5 7v6c0 2.2 4.9 4 11 4s11-1.8 11-4V7c0 2.2-4.9 4-11 4S5 9.2 5 7z"/>'
        f'<path fill="{d}" d="M5 13v6c0 2.2 4.9 4 11 4s11-1.8 11-4v-6c0 2.2-4.9 4-11 4S5 15.2 5 13z"/>'
        f'<path fill="{t}" d="M5 19v6c0 2.2 4.9 4 11 4s11-1.8 11-4v-6c0 2.2-4.9 4-11 4S5 21.2 5 19z"/>'
        f'<ellipse cx="16" cy="7" rx="11" ry="4" fill="none" stroke="{_shade(t, 0.25)}" stroke-width="0.6"/>'
    )


def i_database():
    return i_sql()


def i_prisma():
    cy = C["cyan_alt"]
    return svg(
        f'<path fill="{cy}" d="M16 3l11 22-11 6L5 25z"/>'
        f'<path fill="{_shade(cy, -0.3)}" d="M16 3v28L5 25z" opacity="0.45"/>'
    )


def i_graphql():
    r = C["red"]
    return svg(
        f'<g fill="none" stroke="{r}" stroke-width="1.6">'
        '<polygon points="16,3 27,9.5 27,22.5 16,29 5,22.5 5,9.5"/>'
        '<line x1="16" y1="3" x2="5" y2="22.5"/>'
        '<line x1="16" y1="3" x2="27" y2="22.5"/>'
        '<line x1="5" y1="9.5" x2="27" y2="9.5"/>'
        '<line x1="5" y1="22.5" x2="27" y2="22.5"/>'
        '</g>'
        f'<g fill="{r}">'
        '<circle cx="16" cy="3" r="2"/>'
        '<circle cx="27" cy="9.5" r="2"/>'
        '<circle cx="27" cy="22.5" r="2"/>'
        '<circle cx="16" cy="29" r="2"/>'
        '<circle cx="5" cy="22.5" r="2"/>'
        '<circle cx="5" cy="9.5" r="2"/>'
        '</g>'
    )


def i_git():
    o = C["orange"]
    return svg(
        # diamond
        f'<path fill="{o}" d="M16 2.5l13.5 13.5L16 29.5 2.5 16z"/>'
        # branch
        '<g fill="#fff">'
        '<circle cx="12" cy="13" r="1.8"/>'
        '<circle cx="20" cy="13" r="1.8"/>'
        '<circle cx="16" cy="22" r="1.8"/>'
        '<rect x="11.3" y="13" width="1.4" height="6"/>'
        '<rect x="19.3" y="13" width="1.4" height="3"/>'
        '<path d="M12 19q4 0 4-3" stroke="#fff" stroke-width="1.4" fill="none"/>'
        '<path d="M20 16q0 3-4 3" stroke="#fff" stroke-width="1.4" fill="none"/>'
        '</g>'
    )


def i_gitignore():
    o = C["orange"]
    return svg(
        f'<path fill="{o}" d="M16 2.5l13.5 13.5L16 29.5 2.5 16z"/>'
        # forbid sign
        '<circle cx="16" cy="16" r="6.5" fill="none" stroke="#fff" stroke-width="1.8"/>'
        '<line x1="11.3" y1="11.3" x2="20.7" y2="20.7" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>'
    )


def i_gitattributes():
    o = C["orange"]
    return svg(
        f'<path fill="{o}" d="M16 2.5l13.5 13.5L16 29.5 2.5 16z"/>'
        '<text x="16" y="20" font-family="-apple-system, system-ui, sans-serif" font-size="11" font-weight="800" text-anchor="middle" fill="#fff">A</text>'
    )


def i_gitmodules():
    o = C["orange"]
    return svg(
        f'<path fill="{o}" d="M16 2.5l13.5 13.5L16 29.5 2.5 16z"/>'
        '<g fill="#fff"><rect x="10" y="11" width="5" height="5"/><rect x="17" y="11" width="5" height="5"/><rect x="13.5" y="18" width="5" height="5"/></g>'
    )


# --------------------------------------------------------------------------- #
# Build / package / config tools
# --------------------------------------------------------------------------- #
def i_eslint():
    p = C["purple"]
    return svg(
        # hexagon
        f'<polygon points="16,3 28,9.5 28,22.5 16,29 4,22.5 4,9.5" fill="{p}"/>'
        '<text x="16" y="21" font-family="-apple-system, system-ui, sans-serif" font-size="10" font-weight="800" text-anchor="middle" fill="#0d1620">ES</text>'
    )


def i_prettier():
    c = C["cyan"]
    return svg(
        # rows of dots
        '<g>'
        f'<g fill="{c}">'
        '<circle cx="8" cy="8"  r="1.4"/><circle cx="13" cy="8" r="1.4"/><circle cx="18" cy="8"  r="1.4"/><circle cx="24" cy="8" r="1.4"/>'
        '<circle cx="8" cy="13" r="1.4"/><circle cx="13" cy="13" r="1.4"/><circle cx="18" cy="13" r="1.4"/>'
        '<circle cx="8" cy="18" r="1.4"/><circle cx="13" cy="18" r="1.4"/><circle cx="18" cy="18" r="1.4"/>'
        '<circle cx="8" cy="24" r="1.4"/><circle cx="13" cy="24" r="1.4"/>'
        '</g>'
        '</g>'
    )


def i_editorconfig():
    return svg(
        f'<rect x="2" y="5" width="28" height="22" rx="3" fill="{C["fg_dim"]}"/>'
        '<g fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round">'
        '<line x1="6" y1="11" x2="14" y2="11"/>'
        '<line x1="6" y1="16" x2="20" y2="16"/>'
        '<line x1="6" y1="21" x2="11" y2="21"/>'
        '<line x1="22" y1="11" x2="26" y2="11"/>'
        '</g>'
    )


def i_babel():
    y = C["yellow"]
    return svg(
        # B inside a yellow shape
        f'<path fill="{y}" d="M16 2l13 7v14L16 30 3 23V9z"/>'
        '<text x="16" y="22" font-family="-apple-system, system-ui, sans-serif" font-size="14" font-weight="800" text-anchor="middle" fill="#0d1620">B</text>'
    )


def i_webpack():
    b = C["blue"]
    return svg(
        f'<path fill="{b}" d="M16 2l13 7v14L16 30 3 23V9z"/>'
        # interior lines suggesting bundle
        '<g fill="#fff" opacity="0.95">'
        '<polygon points="16,7 24,11 24,21 16,25 8,21 8,11"/>'
        '</g>'
        f'<g fill="{b}">'
        '<polygon points="16,9 22,12 22,20 16,23 10,20 10,12"/>'
        '</g>'
    )


def i_rollup():
    r = C["red"]
    return svg(
        # bundled rolls
        f'<g fill="{r}">'
        '<circle cx="10" cy="13" r="5"/>'
        '<circle cx="22" cy="13" r="5"/>'
        '<circle cx="16" cy="22" r="5"/>'
        '</g>'
        '<g fill="#0d1620">'
        '<circle cx="10" cy="13" r="1.8"/>'
        '<circle cx="22" cy="13" r="1.8"/>'
        '<circle cx="16" cy="22" r="1.8"/>'
        '</g>'
    )


def i_vite():
    p, y = C["purple"], C["yellow"]
    return svg(
        # lightning bolt
        f'<path fill="{p}" d="M21 2L7 18h7l-2 12 14-16h-7z"/>'
        f'<path fill="{y}" d="M21 2L7 18h7l-2 12 14-16h-7z" opacity="0.5"/>'
    )


def i_parcel():
    o = C["orange"]
    return svg(
        # gift box
        f'<rect x="4" y="10" width="24" height="18" rx="1.5" fill="{o}"/>'
        f'<rect x="4" y="10" width="24" height="4" fill="{_shade(o, -0.25)}"/>'
        f'<rect x="14" y="6" width="4" height="22" fill="{_shade(o, -0.25)}"/>'
        f'<path fill="{o}" d="M11 6q-2 0-2 2t2 2h3V6zm10 0q2 0 2 2t-2 2h-3V6z"/>'
    )


def i_turbo():
    r = C["red"]
    return svg(
        f'<circle cx="16" cy="16" r="13" fill="{r}"/>'
        '<g fill="#fff"><path d="M16 7c5 0 9 4 9 9s-4 9-9 9-9-4-9-9 4-9 9-9zm0 3a6 6 0 1 0 0 12 6 6 0 0 0 0-12z"/>'
        '<path d="M22 4l3 3-3 3-2-2z"/></g>'
    )


def i_nx():
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{C["blue"]}"/>'
        '<text x="16" y="22" font-family="-apple-system, system-ui, sans-serif" font-size="13" font-weight="800" font-style="italic" text-anchor="middle" fill="#fff">Nx</text>'
    )


def i_jest():
    r = C["red"]
    return svg(
        # crown-ish
        f'<path fill="{r}" d="M16 5c-5 0-9 4-9 9 0 4 2 7 5 8l-1 5h10l-1-5c3-1 5-4 5-8 0-5-4-9-9-9z"/>'
        '<g fill="#fff">'
        '<rect x="14" y="11" width="4" height="6" rx="1"/>'
        '<circle cx="11" cy="10" r="1.4"/><circle cx="21" cy="10" r="1.4"/>'
        '</g>'
    )


def i_vitest():
    g = C["green"]
    return svg(
        # checkered lightning
        f'<path fill="{g}" d="M21 2L7 18h7l-2 12 14-16h-7z"/>'
        '<path fill="#0d1620" d="M16 12l-3 4h2l-1 6 4-7h-2z" opacity="0.3"/>'
    )


def i_mocha():
    o = C["orange"]
    return svg(
        # coffee cup
        f'<path fill="{o}" d="M7 12h17v9c0 4-3 6-8 6s-9-2-9-6v-9z"/>'
        f'<path fill="none" stroke="{o}" stroke-width="2" d="M24 13c2 0 4 1.5 4 4s-2 4-4 4"/>'
        '<g fill="#fff">'
        '<path d="M11 6c0 2-2 2-2 4M16 6c0 2-2 2-2 4M21 6c0 2-2 2-2 4" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        '</g>'
    )


def i_cypress():
    g = C["green"]
    return svg(
        f'<circle cx="16" cy="16" r="13" fill="{g}"/>'
        f'<path fill="{C["bg"]}" d="M12 11a5 5 0 0 0 0 10c2 0 4-1.4 4.6-3.3l-2.3-.7c-.3 1-1.3 1.6-2.3 1.6a2.6 2.6 0 1 1 0-5.2c1 0 2 .6 2.3 1.6l2.3-.7A5 5 0 0 0 12 11z"/>'
        f'<circle cx="22" cy="22" r="2" fill="{C["bg"]}"/>'
    )


def i_playwright():
    g = C["green"]
    return svg(
        # play arrow
        f'<path fill="{g}" d="M8 5l18 11L8 27z"/>'
        '<path fill="#0d1620" d="M14 11l8 5-8 5z" opacity="0.6"/>'
    )


def i_storybook():
    c = C["coral"]
    return svg(
        # open book
        f'<path fill="{c}" d="M4 5h11v22H4z"/>'
        f'<path fill="{_shade(c, 0.2)}" d="M28 5H17v22h11z"/>'
        '<g fill="#fff">'
        '<rect x="7" y="9" width="6" height="1.5"/>'
        '<rect x="7" y="13" width="6" height="1.5"/>'
        '<rect x="19" y="9" width="6" height="1.5"/>'
        '<rect x="19" y="13" width="6" height="1.5"/>'
        '</g>'
    )


# --------------------------------------------------------------------------- #
# Package managers / lock
# --------------------------------------------------------------------------- #
def i_npm():
    r = C["red"]
    return svg(
        f'<rect x="2" y="9" width="28" height="14" fill="{r}"/>'
        '<g fill="#fff">'
        '<rect x="5" y="12" width="6" height="8"/><rect x="8" y="14" width="1.5" height="6" fill="' + r + '"/>'
        '<rect x="13" y="12" width="6" height="8"/><rect x="16" y="14" width="1.5" height="4" fill="' + r + '"/>'
        '<rect x="21" y="12" width="6" height="8"/><rect x="24" y="14" width="1.5" height="6" fill="' + r + '"/>'
        '</g>'
    )


def i_yarn():
    cy = C["cyan_alt"]
    return svg(
        f'<circle cx="16" cy="16" r="13" fill="{cy}"/>'
        '<g fill="#0d1620">'
        '<path d="M16 7c-1 0-2 .5-2 1.5 0 .5.3 1 .8 1.5C13 11 12 13 12 16c0 1.5.5 3 1.5 4-.5 1 .5 3 3 3 1.5 0 3-.5 4-1.5h2c1 0 2-.5 2-1.5s-1-1.5-2-1.5h-1c1-2 1.5-4 1-6 0-1.5-1-3-3-3-.5-1-1.5-2-3.5-2z"/>'
        '</g>'
    )


def i_pnpm():
    o = C["orange"]
    return svg(
        '<g fill="' + o + '">'
        '<rect x="5" y="5" width="6" height="6" rx="0.5"/>'
        '<rect x="13" y="5" width="6" height="6" rx="0.5"/>'
        '<rect x="21" y="5" width="6" height="6" rx="0.5"/>'
        '<rect x="13" y="13" width="6" height="6" rx="0.5"/>'
        '<rect x="21" y="13" width="6" height="6" rx="0.5"/>'
        '<rect x="21" y="21" width="6" height="6" rx="0.5"/>'
        '</g>'
        '<g fill="' + C["yellow"] + '">'
        '<rect x="5" y="13" width="6" height="6" rx="0.5"/>'
        '<rect x="5" y="21" width="6" height="6" rx="0.5"/>'
        '<rect x="13" y="21" width="6" height="6" rx="0.5"/>'
        '</g>'
    )


def i_bun():
    y = C["yellow"]
    return svg(
        f'<ellipse cx="16" cy="17" rx="13" ry="11" fill="{y}"/>'
        '<g fill="#0d1620">'
        '<ellipse cx="11" cy="15" rx="1.4" ry="1.6"/>'
        '<ellipse cx="21" cy="15" rx="1.4" ry="1.6"/>'
        '<ellipse cx="16" cy="20" rx="2" ry="1.4"/>'
        '</g>'
    )


def i_lock():
    return svg(
        '<path fill="none" stroke="' + C["fg_dim"] + '" stroke-width="2.5" d="M11 14V10a5 5 0 0 1 10 0v4"/>'
        '<rect x="7" y="14" width="18" height="14" rx="2" fill="' + C["fg_dim"] + '"/>'
        '<circle cx="16" cy="20" r="2" fill="' + C["bg"] + '"/>'
        '<rect x="15" y="20" width="2" height="5" fill="' + C["bg"] + '"/>'
    )


# --------------------------------------------------------------------------- #
# Build systems
# --------------------------------------------------------------------------- #
def i_makefile():
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{C["fg_dim"]}"/>'
        '<g fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M8 22V10l4 6 4-6v12"/>'
        '<path d="M20 10v12M16 18l4-4 4 4"/>'
        '</g>'
    )


def i_cmake():
    b = C["blue"]
    return svg(
        f'<path fill="{b}" d="M16 4l12 22H4z"/>'
        '<path fill="#fff" d="M16 12l5 12H11z"/>'
        f'<path fill="{b}" d="M16 18l2 6h-4z"/>'
    )


def i_gradle():
    c = C["cyan"]
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{c}"/>'
        '<g fill="#0d1620">'
        '<circle cx="9" cy="10" r="1.8"/><circle cx="16" cy="10" r="1.8"/><circle cx="23" cy="10" r="1.8"/>'
        '<path d="M7 16c2 4 16 4 18 0" stroke="#0d1620" stroke-width="2" fill="none"/>'
        '<rect x="10" y="20" width="12" height="3" rx="1"/>'
        '</g>'
    )


def i_maven():
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{C["orange"]}"/>'
        '<g fill="#fff">'
        '<path d="M9 22V10l3 6 3-6v12"/>'
        '<path d="M17 10h6v2h-4v3h3.5v2H19v3h4v2h-6z"/>'
        '</g>'
    )


def i_nuget():
    b = C["blue"]
    return svg(
        f'<circle cx="11" cy="11" r="7" fill="{b}"/>'
        f'<circle cx="21" cy="21" r="7" fill="{b}"/>'
        '<text x="11" y="14.5" font-family="-apple-system, system-ui, sans-serif" font-size="8" font-weight="800" text-anchor="middle" fill="#fff">N</text>'
    )


def i_cargo():
    o = C["orange"]
    return svg(
        # crate
        f'<rect x="4" y="9" width="24" height="18" rx="1.5" fill="{o}"/>'
        f'<g stroke="{_shade(o, -0.3)}" stroke-width="1.4" fill="none">'
        '<line x1="4" y1="14" x2="28" y2="14"/>'
        '<line x1="4" y1="22" x2="28" y2="22"/>'
        '<line x1="11" y1="9" x2="11" y2="27"/>'
        '<line x1="21" y1="9" x2="21" y2="27"/>'
        '</g>'
    )


# --------------------------------------------------------------------------- #
# Misc files (no letter badges — iconic glyphs only)
# --------------------------------------------------------------------------- #
def i_license():
    y = C["yellow"]
    return svg(
        doc_blank(y)
        # ribbon seal
        + '<circle cx="16" cy="20" r="3.5" fill="#0d1620" opacity="0.85"/>'
        + f'<path fill="{y}" d="M13.5 22.5l-1 5 3.5-2 3.5 2-1-5z"/>'
        + '<text x="16" y="21.5" font-family="-apple-system, system-ui, sans-serif" font-size="4.5" font-weight="800" text-anchor="middle" fill="#fff">MIT</text>'
    )


def i_readme():
    cy = C["cyan_alt"]
    return svg(
        doc_blank(C["panel"], _shade(C["panel"], 0.3))
        # info circle
        + f'<circle cx="16" cy="20" r="4.5" fill="{cy}"/>'
        + '<text x="16" y="23" font-family="Georgia, serif" font-size="8" font-style="italic" font-weight="800" text-anchor="middle" fill="#0d1620">i</text>'
    )


def i_changelog():
    p = C["purple"]
    return svg(
        f'<path fill="{p}" d="M5 4h11c2 0 4 1 4 4v20c0-2-2-3-4-3H5z"/>'
        f'<path fill="{_shade(p, 0.2)}" d="M27 4H16c-2 0-4 1-4 4v20c0-2 2-3 4-3h11z"/>'
        # version dot
        '<g fill="#fff">'
        '<circle cx="9"  cy="14" r="1.2"/><rect x="11" y="13.4" width="6" height="1.3"/>'
        '<circle cx="9"  cy="19" r="1.2"/><rect x="11" y="18.4" width="5" height="1.3"/>'
        '<circle cx="21" cy="14" r="1.2"/><rect x="23" y="13.4" width="4" height="1.3"/>'
        '<circle cx="21" cy="19" r="1.2"/><rect x="23" y="18.4" width="3" height="1.3"/>'
        '</g>'
    )


def i_contributing():
    r = C["red"]
    return svg(
        f'<path fill="{r}" d="M16 28C8 22 3 17 3 11.5 3 7.5 6 5 9 5c2 0 4 1 5 3 1-2 3-3 5-3 3 0 6 2.5 6 6.5C28 17 23 22 16 28z"/>'
    )


def i_authors():
    p = C["purple"]
    return svg(
        f'<path fill="{p}" d="M16 5a5 5 0 1 1 0 10 5 5 0 0 1 0-10z"/>'
        f'<path fill="{p}" d="M6 26c0-5 4-9 10-9s10 4 10 9z"/>'
    )


def i_settings():
    return svg(
        f'<g fill="{C["fg_dim"]}"><circle cx="16" cy="16" r="5"/>'
        '<path d="M16 3l2 4-4 0zM16 29l-2-4 4 0zM3 16l4-2 0 4zM29 16l-4 2 0-4zM6.6 6.6l4.2 1.4-2.8 2.8zM25.4 25.4l-4.2-1.4 2.8-2.8zM6.6 25.4l1.4-4.2 2.8 2.8zM25.4 6.6l-1.4 4.2-2.8-2.8z"/>'
        '</g>'
        f'<circle cx="16" cy="16" r="2" fill="{C["bg"]}"/>'
    )


def i_certificate():
    y = C["yellow"]
    return svg(
        doc_blank(C["panel"], _shade(C["panel"], 0.3))
        + f'<g fill="{y}">'
        + '<circle cx="16" cy="17" r="3.5"/>'
        + '<path d="M13.5 19.5l-1 5 3.5-2 3.5 2-1-5z"/>'
        + '</g>'
    )


def i_key():
    y = C["yellow"]
    return svg(
        f'<g fill="{y}">'
        '<circle cx="11" cy="16" r="6"/>'
        '<rect x="14" y="14.5" width="14" height="3"/>'
        '<rect x="22" y="17" width="2.5" height="3"/>'
        '<rect x="26" y="17" width="2" height="4"/>'
        '</g>'
        f'<circle cx="11" cy="16" r="2.2" fill="{C["bg"]}"/>'
    )


def i_image():
    p = C["purple"]
    return svg(
        f'<rect x="3" y="5" width="26" height="22" rx="2" fill="{p}"/>'
        f'<circle cx="11" cy="13" r="2.5" fill="{C["yellow"]}"/>'
        f'<path fill="{_shade(p, 0.3)}" d="M5 25l8-9 6 6 4-4 6 6v2H5z"/>'
    )


def i_svg_icon():
    o = C["orange"]
    return svg(
        doc_blank(o)
        + '<text x="16" y="24" font-family="-apple-system, system-ui, sans-serif" font-size="6.5" font-weight="800" text-anchor="middle" fill="#fff">SVG</text>'
    )


def i_font():
    r = C["red"]
    return svg(
        doc_blank(r)
        + '<text x="16" y="26" font-family="Georgia, serif" font-size="16" font-weight="800" font-style="italic" text-anchor="middle" fill="#fff">F</text>'
    )


def i_archive():
    y = C["yellow"]
    return svg(
        f'<rect x="4" y="3" width="24" height="26" rx="2" fill="{y}"/>'
        f'<g fill="{_shade(y, -0.3)}">'
        '<rect x="14" y="3" width="4" height="3"/>'
        '<rect x="14" y="9" width="4" height="3"/>'
        '<rect x="14" y="15" width="4" height="3"/>'
        '</g>'
        f'<rect x="13" y="20" width="6" height="6" fill="{C["bg"]}"/>'
    )


def i_audio():
    p = C["purple"]
    return svg(
        f'<path fill="{p}" d="M21 4v16.5a4 4 0 1 1-3-3.9V8l-8 1.5v13.6a4 4 0 1 1-3-3.9V7z"/>'
    )


def i_video():
    r = C["red"]
    return svg(
        f'<rect x="2" y="6" width="28" height="20" rx="2" fill="{r}"/>'
        '<path fill="#fff" d="M13 11l8 5-8 5z"/>'
    )


def i_pdf():
    r = C["red"]
    return svg(
        doc_blank(r)
        + '<text x="16" y="25" font-family="-apple-system, system-ui, sans-serif" font-size="6.5" font-weight="800" text-anchor="middle" fill="#fff">PDF</text>'
    )


def i_word():
    return svg(
        doc_blank(C["blue"])
        + '<text x="16" y="25" font-family="-apple-system, system-ui, sans-serif" font-size="11" font-weight="800" text-anchor="middle" fill="#fff">W</text>'
    )


def i_excel():
    return svg(
        doc_blank(C["green"])
        + '<text x="16" y="25" font-family="-apple-system, system-ui, sans-serif" font-size="11" font-weight="800" text-anchor="middle" fill="#0d1620">X</text>'
    )


def i_powerpoint():
    return svg(
        doc_blank(C["orange"])
        + '<text x="16" y="25" font-family="-apple-system, system-ui, sans-serif" font-size="11" font-weight="800" text-anchor="middle" fill="#0d1620">P</text>'
    )


def i_notebook():
    o = C["orange"]
    return svg(
        # jupyter logo-ish
        f'<g fill="{o}">'
        '<path d="M9 11a7 7 0 0 1 14 0z"/>'
        '<path d="M23 17a7 7 0 0 1-14 0z"/>'
        '<circle cx="9" cy="6" r="1.6"/>'
        '<circle cx="23" cy="26" r="1.6"/>'
        '</g>'
    )


def i_disc():
    return svg(
        f'<circle cx="16" cy="16" r="13" fill="{C["fg_dim"]}"/>'
        f'<circle cx="16" cy="16" r="4" fill="{C["bg"]}"/>'
        f'<circle cx="16" cy="16" r="1.6" fill="{C["fg_dim"]}"/>'
    )


def i_vm():
    return svg(
        f'<rect x="3" y="5" width="26" height="22" rx="2" fill="{C["purple"]}"/>'
        f'<rect x="6" y="8" width="20" height="13" rx="1" fill="{C["bg"]}"/>'
        '<text x="16" y="17" font-family="-apple-system, system-ui, sans-serif" font-size="7" font-weight="800" text-anchor="middle" fill="#c792ea">VM</text>'
        f'<rect x="12" y="22" width="8" height="3" fill="{_shade(C["purple"], -0.2)}"/>'
    )


def i_binary():
    return svg(
        doc_blank(C["fg_dim"])
        + '<g fill="#fff" font-family="ui-monospace, monospace" font-size="3.6" font-weight="700">'
        + '<text x="9" y="16">01001</text>'
        + '<text x="9" y="21">10110</text>'
        + '<text x="9" y="26">01101</text>'
        + '</g>'
    )


def i_exe():
    return svg(
        f'<rect x="2" y="2" width="28" height="28" rx="4" fill="{C["fg_dim"]}"/>'
        '<g fill="#fff">'
        '<rect x="6" y="6" width="9" height="9"/>'
        '<rect x="17" y="6" width="9" height="9"/>'
        '<rect x="6" y="17" width="9" height="9"/>'
        '</g>'
    )


# --------------------------------------------------------------------------- #
# Folder glyph factory — accepts a name keyword and returns the right glyph
# --------------------------------------------------------------------------- #
FOLDER_GLYPHS: dict[str, str] = {
    "src":          _glyph_braces(),
    "dist":         _glyph_dl(),
    "build":        _glyph_gear(),
    "out":          _glyph_dl(),
    "bin":          _glyph_box(),
    "lib":          _glyph_cube(),
    "public":       _glyph_globe(),
    "static":       _glyph_globe(),
    "assets":       _glyph_image(),
    "images":       _glyph_image(),
    "icons":        _glyph_image(),
    "fonts":        '<text x="16" y="24" font-family="Georgia, serif" font-size="13" font-style="italic" font-weight="800" text-anchor="middle" fill="#fff">F</text>',
    "css":          '<text x="16" y="23" font-family="-apple-system, system-ui, sans-serif" font-size="7" font-weight="800" text-anchor="middle" fill="#fff">CSS</text>',
    "styles":       '<text x="16" y="23" font-family="-apple-system, system-ui, sans-serif" font-size="7" font-weight="800" text-anchor="middle" fill="#fff">CSS</text>',
    "scss":         '<text x="16" y="24" font-family="-apple-system, system-ui, sans-serif" font-size="9" font-weight="800" text-anchor="middle" fill="#fff">#</text>',
    "components":   _glyph_cube(),
    "pages":        _glyph_page(),
    "views":        _glyph_page(),
    "layouts":      '<g fill="#fff"><rect x="11" y="15" width="10" height="2.5"/><rect x="11" y="19" width="4" height="6"/><rect x="17" y="19" width="4" height="6"/></g>',
    "hooks":        _glyph_hook(),
    "utils":        _glyph_wrench(),
    "helpers":      _glyph_wrench(),
    "services":     _glyph_gear(),
    "api":          _glyph_arrows(),
    "controllers":  '<g fill="none" stroke="#fff" stroke-width="1.6"><circle cx="16" cy="20.5" r="3"/><line x1="16" y1="14" x2="16" y2="17"/><line x1="16" y1="24" x2="16" y2="27"/><line x1="10" y1="20.5" x2="13" y2="20.5"/><line x1="19" y1="20.5" x2="22" y2="20.5"/></g>',
    "models":       _glyph_cube(),
    "schemas":      _glyph_cube(),
    "routes":       _glyph_route(),
    "middleware":   '<g fill="none" stroke="#fff" stroke-width="1.6"><path d="M10 20.5h12M14 17l-4 3.5 4 3.5M18 17l4 3.5-4 3.5"/></g>',
    "store":        _glyph_box(),
    "context":      _glyph_circle_dot(),
    "providers":    _glyph_circle_dot(),
    "types":        '<text x="16" y="24" font-family="-apple-system, system-ui, sans-serif" font-size="8" font-weight="800" text-anchor="middle" fill="#fff">{T}</text>',
    "interfaces":   '<g fill="none" stroke="#fff" stroke-width="1.6"><rect x="11" y="15" width="10" height="11" rx="1.5"/><line x1="13" y1="19" x2="19" y2="19"/><line x1="13" y1="22" x2="17" y2="22"/></g>',
    "config":       _glyph_gear(),
    "tests":        _glyph_test_tube(),
    "docs":         _glyph_book(),
    "scripts":      _glyph_terminal(),
    "tools":        _glyph_wrench(),
    "vendor":       _glyph_box(),
    "node_modules": '<g fill="#fff"><circle cx="11" cy="16" r="2"/><circle cx="21" cy="16" r="2"/><circle cx="16" cy="24" r="2"/><line x1="11" y1="16" x2="16" y2="24" stroke="#fff" stroke-width="1.4"/><line x1="21" y1="16" x2="16" y2="24" stroke="#fff" stroke-width="1.4"/><line x1="11" y1="16" x2="21" y2="16" stroke="#fff" stroke-width="1.4"/></g>',
    "packages":     _glyph_box(),
    "modules":      _glyph_cube(),
    "git":          _glyph_branch(),
    "vscode":       _glyph_gear(),
    "github":       '<g fill="#fff"><path d="M16 13a5 5 0 0 0-1.6 9.7c.3 0 .4-.1.4-.3v-1c-1.3.3-1.7-.6-1.7-.6-.2-.5-.5-.7-.5-.7-.4-.3 0-.3 0-.3.5 0 .7.5.7.5.4.7 1.1.5 1.4.4 0-.3.2-.5.3-.7-1 0-2.1-.5-2.1-2.2 0-.5.2-.9.5-1.2 0-.1-.2-.6 0-1.2 0 0 .4-.1 1.3.5a4.5 4.5 0 0 1 2.4 0c.9-.6 1.3-.5 1.3-.5.2.6 0 1.1 0 1.2.3.3.5.7.5 1.2 0 1.7-1.1 2.1-2.1 2.2.2.1.3.4.3.9v1.3c0 .2.1.4.4.3A5 5 0 0 0 16 13z"/></g>',
    "idea":         '<text x="16" y="25" font-family="-apple-system, system-ui, sans-serif" font-size="9" font-weight="800" text-anchor="middle" fill="#fff">IJ</text>',
    "husky":        '<g fill="#fff"><circle cx="13" cy="19" r="1"/><circle cx="19" cy="19" r="1"/><path d="M14 22q2 1 4 0" stroke="#fff" stroke-width="1.2" fill="none" stroke-linecap="round"/><path d="M11 16l2-2M21 16l-2-2" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/></g>',
    "next":         '<text x="16" y="25" font-family="-apple-system, system-ui, sans-serif" font-size="10" font-weight="800" text-anchor="middle" fill="#fff">N</text>',
    "nuxt":         '<g fill="#fff"><path d="M16 14l-5 10h10z"/></g>',
    "svelte":       '<text x="16" y="25" font-family="Georgia, serif" font-size="13" font-style="italic" font-weight="800" text-anchor="middle" fill="#fff">s</text>',
    "target":       '<g fill="none" stroke="#fff" stroke-width="1.5"><circle cx="16" cy="20.5" r="5"/><circle cx="16" cy="20.5" r="2.5"/><circle cx="16" cy="20.5" r="0.6" fill="#fff"/></g>',
    "coverage":     _glyph_check(),
    "environment":  _glyph_gear(),
    "secrets":      _glyph_lock(),
    "locales":      _glyph_globe(),
    "database":     _glyph_db(),
    "migrations":   '<g fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round"><path d="M11 18h7M15 15l3 3-3 3"/><path d="M21 23h-7M17 26l-3-3 3-3"/></g>',
    "seeders":      '<g fill="#fff"><circle cx="16" cy="20.5" r="2"/><circle cx="11" cy="16" r="1.5"/><circle cx="21" cy="16" r="1.5"/><circle cx="11" cy="25" r="1.5"/><circle cx="21" cy="25" r="1.5"/></g>',
    "prisma":       '<path fill="#fff" d="M16 13l5 11-5 3-5-3z"/>',
    "mocks":        '<g fill="#fff"><circle cx="13" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><circle cx="13" cy="19" r="0.8" fill="#0d1620"/><circle cx="19" cy="19" r="0.8" fill="#0d1620"/></g>',
    "examples":     _glyph_info(),
    "plugins":      '<g fill="#fff"><rect x="11" y="14" width="3" height="4" rx="0.5"/><rect x="18" y="14" width="3" height="4" rx="0.5"/><path d="M14 18h4v6c0 1-1 2-2 2s-2-1-2-2v-6z"/></g>',
    "themes":       '<g fill="#fff"><circle cx="14" cy="17" r="3"/><circle cx="19" cy="17" r="3" opacity="0.7"/><circle cx="16.5" cy="22" r="3" opacity="0.5"/></g>',
    "server":       '<g fill="#fff"><rect x="11" y="14" width="10" height="4" rx="0.5"/><rect x="11" y="19" width="10" height="4" rx="0.5"/><circle cx="13" cy="16" r="0.6" fill="#0d1620"/><circle cx="13" cy="21" r="0.6" fill="#0d1620"/></g>',
    "client":       '<g fill="none" stroke="#fff" stroke-width="1.6"><rect x="10" y="14" width="12" height="9" rx="1"/><line x1="13" y1="26" x2="19" y2="26"/></g>',
    "shared":       '<g fill="none" stroke="#fff" stroke-width="1.6"><circle cx="13" cy="17" r="2"/><circle cx="20" cy="17" r="2"/><circle cx="16.5" cy="23" r="2"/><line x1="14" y1="18.5" x2="15.5" y2="22"/><line x1="19" y1="18.5" x2="17.5" y2="22"/></g>',
    "common":       _glyph_cube(),
    "core":         '<g fill="#fff"><circle cx="16" cy="20" r="5"/><circle cx="16" cy="20" r="2" fill="#0d1620"/></g>',
    "frontend":     '<g fill="none" stroke="#fff" stroke-width="1.6"><rect x="10" y="14" width="12" height="9" rx="1"/><line x1="10" y1="17.5" x2="22" y2="17.5"/><circle cx="12" cy="15.7" r="0.5" fill="#fff"/></g>',
    "backend":      '<g fill="#fff"><rect x="11" y="14" width="10" height="4" rx="0.5"/><rect x="11" y="19" width="10" height="4" rx="0.5"/></g>',
    "admin":        _glyph_gear(),
    "auth":         _glyph_lock(),
    "constants":    '<text x="16" y="24" font-family="-apple-system, system-ui, sans-serif" font-size="9" font-weight="800" text-anchor="middle" fill="#fff">K</text>',
    "dto":          '<text x="16" y="24" font-family="-apple-system, system-ui, sans-serif" font-size="6.5" font-weight="800" text-anchor="middle" fill="#fff">DTO</text>',
    "entity":       _glyph_cube(),
    "repository":   '<g fill="#fff"><rect x="11" y="14" width="10" height="9" rx="0.8"/><rect x="13" y="17" width="6" height="2" fill="#0d1620"/></g>',
    "ci":           '<g fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="20.5" r="1.4" fill="#fff"/><line x1="13.5" y1="20.5" x2="18.5" y2="20.5"/><circle cx="20" cy="20.5" r="1.4" fill="#fff"/></g>',
    "docker":       '<g fill="#fff"><rect x="11" y="18" width="3" height="3"/><rect x="14.5" y="18" width="3" height="3"/><rect x="18" y="18" width="3" height="3"/><path d="M10 22h12c0 1.5-2 3-5 3s-7-1.5-7-3z"/></g>',
    "logs":         _glyph_terminal(),
    "temp":         '<g fill="#fff"><circle cx="14" cy="18" r="2"/><circle cx="20" cy="22" r="2"/></g>',
    "cache":        '<g fill="none" stroke="#fff" stroke-width="1.6"><ellipse cx="16" cy="16" rx="6" ry="2.4"/><path d="M10 16v6c0 1.3 2.7 2.4 6 2.4s6-1.1 6-2.4v-6"/></g>',
    "downloads":    _glyph_dl(),
    "uploads":      _glyph_ul(),
    "video":        '<g fill="#fff"><rect x="11" y="15" width="10" height="9" rx="1"/><path d="M14 18l5 3-5 3z" fill="#0d1620"/></g>',
    "audio":        '<path fill="#fff" d="M20 13v9.5a2.5 2.5 0 1 1-2-2.4V15l-4 .8v8.7a2.5 2.5 0 1 1-2-2.4v-7z"/>',
}


# --------------------------------------------------------------------------- #
# Icon catalogue
# --------------------------------------------------------------------------- #
ICONS: dict[str, str] = {}


def add(name: str, content: str) -> None:
    ICONS[name] = content


# default file & folder
add("file", svg(doc_blank(C["fg_dim"])))
add("file_light", svg(doc_blank(C["fg"])))
add("folder", folder_closed(C["teal"]))
add("folder_open", folder_open(C["teal"]))
add("folder_root", folder_closed(C["cyan_alt"]))
add("folder_root_open", folder_open(C["cyan_alt"]))

# languages / frameworks
add("typescript",      i_typescript())
add("typescript_def",  i_typescript_def())
add("javascript",      i_javascript())
add("react",           i_react())
add("react_ts",        i_react())
add("vue",             i_vue())
add("angular",         i_angular())
add("svelte",          i_svelte())
add("astro",           i_astro())
add("html",            i_html())
add("css",             i_css())
add("scss",            i_scss())
add("sass",            i_sass())
add("less",            i_less())
add("stylus",          i_stylus())
add("python",          i_python())
add("python_misc",     svg(doc_code(C["blue"])))
add("java",            i_java())
add("class",           i_class())
add("jar",             i_jar())
add("kotlin",          i_kotlin())
add("groovy",          i_groovy())
add("scala",           i_scala())
add("clojure",         i_clojure())
add("go",              i_go())
add("rust",            i_rust())
add("ruby",            i_ruby())
add("swift",           i_swift())
add("dart",            i_dart())
add("php",             i_php())
add("csharp",          i_csharp())
add("cpp",             i_cpp())
add("c",               i_c())
add("header",          i_header())
add("objective_c",     i_objective_c())
add("perl",            i_perl())
add("lua",             i_lua())
add("haskell",         i_haskell())
add("elixir",          i_elixir())
add("erlang",          i_erlang())
add("r_lang",          i_r_lang())
add("julia",           i_julia())
add("zig",             i_zig())

# data / config / markup
add("json",            i_json())
add("yaml",            i_yaml())
add("xml",             i_xml())
add("toml",            i_toml())
add("ini",             i_ini())
add("conf",            i_conf())
add("env",             i_env())
add("markdown",        i_markdown())
add("mdx",             i_mdx())
add("rst",             i_rst())
add("text",            i_text())
add("log",             i_log())
add("csv",             i_csv())
add("tsv",             i_tsv())
add("tex",             i_tex())

# shells / docker / db / git
add("shell",           i_shell())
add("bash",            i_bash())
add("zsh",             i_zsh())
add("fish",            i_fish())
add("powershell",      i_powershell())
add("batch",           i_batch())
add("docker",          i_docker())
add("docker_compose",  i_docker_compose())
add("sql",             i_sql())
add("database",        i_database())
add("prisma",          i_prisma())
add("graphql",         i_graphql())
add("git",             i_git())
add("gitignore",       i_gitignore())
add("gitattributes",   i_gitattributes())
add("gitmodules",      i_gitmodules())

# tooling
add("eslint",          i_eslint())
add("prettier",        i_prettier())
add("editorconfig",    i_editorconfig())
add("babel",           i_babel())
add("webpack",         i_webpack())
add("rollup",          i_rollup())
add("vite",            i_vite())
add("parcel",          i_parcel())
add("turbo",           i_turbo())
add("nx",              i_nx())
add("jest",            i_jest())
add("vitest",          i_vitest())
add("mocha",           i_mocha())
add("cypress",         i_cypress())
add("playwright",      i_playwright())
add("storybook",       i_storybook())

# package managers / lock
add("npm",             i_npm())
add("yarn",            i_yarn())
add("pnpm",            i_pnpm())
add("bun",             i_bun())
add("lock",            i_lock())

# build systems
add("makefile",        i_makefile())
add("cmake",           i_cmake())
add("gradle",          i_gradle())
add("maven",           i_maven())
add("nuget",           i_nuget())
add("cargo",           i_cargo())

# misc files
add("license",         i_license())
add("readme",          i_readme())
add("changelog",       i_changelog())
add("contributing",    i_contributing())
add("authors",         i_authors())
add("settings",        i_settings())
add("certificate",     i_certificate())
add("key",             i_key())
add("image",           i_image())
add("svg_icon",        i_svg_icon())
add("font",            i_font())
add("archive",         i_archive())
add("audio",           i_audio())
add("video",           i_video())
add("pdf",             i_pdf())
add("word",            i_word())
add("excel",           i_excel())
add("powerpoint",      i_powerpoint())
add("notebook",        i_notebook())
add("disc",            i_disc())
add("vm",              i_vm())
add("binary",          i_binary())
add("exe",             i_exe())


# --------------------------------------------------------------------------- #
# Folder catalogue — (name -> base color)
# --------------------------------------------------------------------------- #
FOLDER_DEFS: list[tuple[str, str]] = [
    ("src",          C["blue"]),
    ("dist",         C["orange"]),
    ("build",        C["orange"]),
    ("out",          C["orange"]),
    ("bin",          C["orange"]),
    ("lib",          C["purple"]),
    ("public",       C["cyan"]),
    ("static",       C["cyan"]),
    ("assets",       C["yellow"]),
    ("images",       C["purple"]),
    ("icons",        C["yellow"]),
    ("fonts",        C["red"]),
    ("css",          C["blue"]),
    ("styles",       C["blue"]),
    ("scss",         C["red"]),
    ("components",   C["purple"]),
    ("pages",        C["cyan_alt"]),
    ("views",        C["cyan_alt"]),
    ("layouts",      C["cyan_alt"]),
    ("hooks",        C["purple"]),
    ("utils",        C["yellow"]),
    ("helpers",      C["yellow"]),
    ("services",     C["green"]),
    ("api",          C["green"]),
    ("controllers",  C["orange"]),
    ("models",       C["blue"]),
    ("schemas",      C["blue"]),
    ("routes",       C["cyan"]),
    ("middleware",   C["purple"]),
    ("store",        C["yellow"]),
    ("context",      C["purple"]),
    ("providers",    C["purple"]),
    ("types",        C["cyan_alt"]),
    ("interfaces",   C["green"]),
    ("config",       C["fg_dim"]),
    ("tests",        C["green"]),
    ("docs",         C["cyan_alt"]),
    ("scripts",      C["green"]),
    ("tools",        C["fg_dim"]),
    ("vendor",       C["fg_dim"]),
    ("node_modules", C["red"]),
    ("packages",     C["red"]),
    ("modules",      C["red"]),
    ("git",          C["orange"]),
    ("vscode",       C["blue"]),
    ("github",       C["purple"]),
    ("idea",         C["yellow"]),
    ("husky",        C["cyan"]),
    ("next",         C["fg"]),
    ("nuxt",         C["green"]),
    ("svelte",       C["orange"]),
    ("target",       C["orange"]),
    ("coverage",     C["green"]),
    ("environment",  C["yellow"]),
    ("secrets",      C["red"]),
    ("locales",      C["cyan"]),
    ("database",     C["teal"]),
    ("migrations",   C["orange"]),
    ("seeders",      C["green"]),
    ("prisma",       C["cyan"]),
    ("mocks",        C["yellow"]),
    ("examples",     C["purple"]),
    ("plugins",      C["purple"]),
    ("themes",       C["cyan"]),
    ("server",       C["blue"]),
    ("client",       C["cyan"]),
    ("shared",       C["yellow"]),
    ("common",       C["yellow"]),
    ("core",         C["red"]),
    ("frontend",     C["cyan"]),
    ("backend",      C["blue"]),
    ("admin",        C["orange"]),
    ("auth",         C["red"]),
    ("constants",    C["orange"]),
    ("dto",          C["green"]),
    ("entity",       C["green"]),
    ("repository",   C["yellow"]),
    ("ci",           C["cyan_alt"]),
    ("docker",       C["blue"]),
    ("logs",         C["fg_dim"]),
    ("temp",         C["fg_dim"]),
    ("cache",        C["fg_dim"]),
    ("downloads",    C["green"]),
    ("uploads",      C["red"]),
    ("video",        C["red"]),
    ("audio",        C["purple"]),
]

for name, color in FOLDER_DEFS:
    glyph = FOLDER_GLYPHS.get(name, "")
    add(f"folder_{name}",       folder_closed(color, glyph))
    add(f"folder_{name}_open",  folder_open(color, glyph))


# --------------------------------------------------------------------------- #
# Icon-theme JSON mapping
# --------------------------------------------------------------------------- #
def icon_path(name: str) -> str:
    return f"./icons/{name}.svg"


THEME: dict = {
    "iconDefinitions": {name: {"iconPath": icon_path(name)} for name in ICONS},
    "file": "file",
    "folder": "folder",
    "folderExpanded": "folder_open",
    "rootFolder": "folder_root",
    "rootFolderExpanded": "folder_root_open",
    "folderNames": {},
    "folderNamesExpanded": {},
    "fileExtensions": {},
    "fileNames": {},
    "languageIds": {},
    "hidesExplorerArrows": False,
}


# ---- File extensions ---- #
EXTENSIONS: dict[str, str] = {
    "js": "javascript", "mjs": "javascript", "cjs": "javascript",
    "jsx": "react",
    "ts": "typescript", "mts": "typescript", "cts": "typescript",
    "tsx": "react_ts",
    "vue": "vue", "svelte": "svelte", "astro": "astro",
    "html": "html", "htm": "html", "xhtml": "html",
    "css": "css", "scss": "scss", "sass": "sass", "less": "less", "styl": "stylus",
    "py": "python", "pyc": "python_misc", "pyi": "python_misc", "pyw": "python_misc", "ipynb": "notebook",
    "java": "java", "class": "class", "jar": "jar",
    "kt": "kotlin", "kts": "kotlin",
    "groovy": "groovy", "gradle": "gradle",
    "scala": "scala", "sbt": "scala",
    "clj": "clojure", "cljs": "clojure",
    "c": "c", "h": "header", "hh": "header", "hpp": "header",
    "cpp": "cpp", "cxx": "cpp", "cc": "cpp",
    "cs": "csharp", "csproj": "csharp", "sln": "csharp",
    "m": "objective_c", "mm": "objective_c",
    "go": "go", "mod": "go", "sum": "go",
    "rs": "rust",
    "swift": "swift",
    "dart": "dart",
    "php": "php", "phtml": "php", "blade.php": "php",
    "rb": "ruby", "erb": "ruby", "gemspec": "ruby",
    "pl": "perl", "pm": "perl",
    "lua": "lua",
    "hs": "haskell",
    "ex": "elixir", "exs": "elixir",
    "erl": "erlang",
    "r": "r_lang", "rmd": "r_lang",
    "jl": "julia",
    "zig": "zig",
    "json": "json", "json5": "json", "jsonc": "json",
    "yml": "yaml", "yaml": "yaml",
    "xml": "xml", "xsl": "xml", "xsd": "xml",
    "toml": "toml",
    "ini": "ini", "cfg": "conf", "conf": "conf", "properties": "conf",
    "env": "env",
    "md": "markdown", "markdown": "markdown", "mdx": "mdx",
    "rst": "rst", "txt": "text", "log": "log",
    "tex": "tex", "csv": "csv", "tsv": "tsv",
    "sh": "shell", "bash": "bash", "zsh": "zsh", "fish": "fish",
    "ps1": "powershell", "psm1": "powershell",
    "bat": "batch", "cmd": "batch",
    "sql": "sql", "mysql": "sql", "pgsql": "sql", "psql": "sql",
    "db": "database", "sqlite": "database", "sqlite3": "database",
    "prisma": "prisma",
    "graphql": "graphql", "gql": "graphql",
    "lock": "lock",
    "png": "image", "jpg": "image", "jpeg": "image", "gif": "image",
    "webp": "image", "bmp": "image", "tiff": "image", "tif": "image",
    "ico": "image", "icns": "image", "avif": "image",
    "svg": "svg_icon",
    "ttf": "font", "otf": "font", "woff": "font", "woff2": "font", "eot": "font",
    "zip": "archive", "tar": "archive", "gz": "archive", "bz2": "archive",
    "xz": "archive", "rar": "archive", "7z": "archive", "tgz": "archive",
    "mp3": "audio", "wav": "audio", "flac": "audio", "ogg": "audio",
    "aac": "audio", "m4a": "audio",
    "mp4": "video", "mkv": "video", "mov": "video", "webm": "video",
    "avi": "video", "flv": "video",
    "pdf": "pdf", "doc": "word", "docx": "word",
    "xls": "excel", "xlsx": "excel",
    "ppt": "powerpoint", "pptx": "powerpoint",
    "iso": "disc", "img": "disc", "dmg": "disc",
    "ova": "vm", "vmdk": "vm", "vdi": "vm",
    "bin": "binary", "dll": "binary", "so": "binary", "dylib": "binary",
    "exe": "exe", "msi": "exe", "app": "exe",
    "crt": "certificate", "cer": "certificate", "pem": "certificate",
    "p12": "certificate", "pfx": "certificate",
    "key": "key", "pub": "key",
}
THEME["fileExtensions"].update(EXTENSIONS)


# ---- File names ---- #
FILE_NAMES: dict[str, str] = {
    "readme.md": "readme", "readme.txt": "readme", "readme": "readme",
    "license": "license", "license.md": "license", "license.txt": "license",
    "licence": "license", "licence.md": "license",
    "changelog": "changelog", "changelog.md": "changelog", "history.md": "changelog",
    "contributing": "contributing", "contributing.md": "contributing",
    "code_of_conduct.md": "contributing",
    "authors": "authors", "authors.md": "authors",
    "package.json": "npm", "package-lock.json": "npm",
    "npm-shrinkwrap.json": "npm",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm", "pnpm-workspace.yaml": "pnpm",
    "bun.lockb": "bun",
    "tsconfig.json": "typescript_def",
    "tsconfig.app.json": "typescript_def",
    "tsconfig.node.json": "typescript_def",
    "tsconfig.build.json": "typescript_def",
    "tsconfig.base.json": "typescript_def",
    "jsconfig.json": "javascript",
    "webpack.config.js": "webpack", "webpack.config.ts": "webpack",
    "rollup.config.js": "rollup", "rollup.config.ts": "rollup",
    "vite.config.js": "vite", "vite.config.ts": "vite",
    "vitest.config.js": "vitest", "vitest.config.ts": "vitest",
    "parcel.config.js": "parcel",
    "turbo.json": "turbo", "nx.json": "nx",
    "babel.config.js": "babel", "babel.config.json": "babel",
    ".babelrc": "babel", ".babelrc.js": "babel", ".babelrc.json": "babel",
    ".eslintrc": "eslint", ".eslintrc.js": "eslint", ".eslintrc.json": "eslint",
    ".eslintrc.yml": "eslint",
    "eslint.config.js": "eslint", "eslint.config.mjs": "eslint",
    ".prettierrc": "prettier", ".prettierrc.js": "prettier",
    ".prettierrc.json": "prettier", ".prettierrc.yml": "prettier",
    "prettier.config.js": "prettier",
    ".editorconfig": "editorconfig",
    "jest.config.js": "jest", "jest.config.ts": "jest", "jest.setup.js": "jest",
    "cypress.config.js": "cypress", "cypress.config.ts": "cypress",
    "playwright.config.js": "playwright", "playwright.config.ts": "playwright",
    ".mocharc.js": "mocha", ".mocharc.json": "mocha",
    "storybook.config.js": "storybook",
    "dockerfile": "docker", ".dockerignore": "docker",
    "docker-compose.yml": "docker_compose", "docker-compose.yaml": "docker_compose",
    "compose.yml": "docker_compose", "compose.yaml": "docker_compose",
    ".gitignore": "gitignore",
    ".gitattributes": "gitattributes",
    ".gitmodules": "gitmodules",
    ".gitkeep": "git", ".gitconfig": "git",
    "requirements.txt": "python_misc", "requirements-dev.txt": "python_misc",
    "pipfile": "python_misc", "pipfile.lock": "lock",
    "pyproject.toml": "python_misc", "setup.py": "python",
    "setup.cfg": "python_misc", "tox.ini": "python_misc",
    "manage.py": "python",
    "pom.xml": "maven",
    "build.gradle": "gradle", "build.gradle.kts": "gradle",
    "settings.gradle": "gradle", "settings.gradle.kts": "gradle",
    "gradlew": "gradle", "gradlew.bat": "gradle",
    "gradle.properties": "gradle",
    "cargo.toml": "cargo", "cargo.lock": "lock",
    "go.mod": "go", "go.sum": "go",
    "gemfile": "ruby", "gemfile.lock": "lock", "rakefile": "ruby",
    "composer.json": "php", "composer.lock": "lock",
    "makefile": "makefile", "gnumakefile": "makefile",
    "cmakelists.txt": "cmake",
    ".env": "env", ".env.example": "env", ".env.local": "env",
    ".env.development": "env", ".env.production": "env", ".env.test": "env",
    ".nvmrc": "javascript", ".node-version": "javascript",
    ".python-version": "python", ".ruby-version": "ruby",
    ".tool-versions": "settings",
    ".huskyrc": "settings", ".lintstagedrc": "settings",
    ".browserslistrc": "settings",
    "vercel.json": "settings", "netlify.toml": "settings",
    "firebase.json": "settings", "now.json": "settings",
    "renovate.json": "settings", ".releaserc": "settings",
    "release-please-config.json": "settings",
}
THEME["fileNames"].update(FILE_NAMES)


# ---- Language IDs ---- #
LANGUAGE_IDS: dict[str, str] = {
    "javascript": "javascript", "javascriptreact": "react",
    "typescript": "typescript", "typescriptreact": "react_ts",
    "html": "html", "css": "css", "scss": "scss", "sass": "sass", "less": "less",
    "vue": "vue", "svelte": "svelte",
    "python": "python", "java": "java",
    "kotlin": "kotlin", "groovy": "groovy", "scala": "scala", "clojure": "clojure",
    "go": "go", "rust": "rust", "ruby": "ruby", "swift": "swift", "dart": "dart",
    "php": "php", "csharp": "csharp",
    "c": "c", "cpp": "cpp", "objective-c": "objective_c", "objective-cpp": "objective_c",
    "perl": "perl", "lua": "lua", "haskell": "haskell",
    "elixir": "elixir", "erlang": "erlang", "r": "r_lang", "julia": "julia", "zig": "zig",
    "json": "json", "jsonc": "json", "yaml": "yaml", "xml": "xml",
    "toml": "toml", "ini": "ini",
    "markdown": "markdown", "mdx": "mdx",
    "restructuredtext": "rst", "plaintext": "text", "log": "log", "latex": "tex",
    "shellscript": "shell", "bat": "batch", "powershell": "powershell",
    "sql": "sql", "prisma": "prisma", "graphql": "graphql",
    "dockerfile": "docker", "ignore": "gitignore",
}
THEME["languageIds"].update(LANGUAGE_IDS)


# ---- Folder name aliases ---- #
FOLDER_ALIASES: dict[str, str] = {
    "src": "src", "source": "src", "sources": "src",
    "dist": "dist", "out": "out", "build": "build", "bin": "bin",
    "lib": "lib", "libs": "lib",
    "public": "public", "static": "static",
    "assets": "assets", "asset": "assets", "resources": "assets", "res": "assets",
    "images": "images", "image": "images", "img": "images",
    "imgs": "images", "pictures": "images",
    "icons": "icons", "icon": "icons",
    "fonts": "fonts", "font": "fonts",
    "css": "css", "styles": "styles", "style": "styles",
    "stylesheet": "styles", "stylesheets": "styles",
    "scss": "scss", "sass": "scss",
    "components": "components", "component": "components",
    "pages": "pages", "page": "pages",
    "views": "views", "view": "views",
    "layouts": "layouts", "layout": "layouts",
    "hooks": "hooks", "hook": "hooks",
    "utils": "utils", "util": "utils",
    "helpers": "helpers", "helper": "helpers",
    "services": "services", "service": "services",
    "api": "api", "apis": "api",
    "controllers": "controllers", "controller": "controllers",
    "models": "models", "model": "models",
    "schemas": "schemas", "schema": "schemas",
    "routes": "routes", "router": "routes", "routing": "routes",
    "middleware": "middleware", "middlewares": "middleware",
    "store": "store", "stores": "store", "state": "store",
    "context": "context", "contexts": "context",
    "providers": "providers", "provider": "providers",
    "types": "types", "type": "types",
    "interfaces": "interfaces", "interface": "interfaces",
    "config": "config", "configs": "config", "conf": "config", "settings": "config",
    "tests": "tests", "test": "tests", "__tests__": "tests",
    "spec": "tests", "specs": "tests", "e2e": "tests",
    "docs": "docs", "doc": "docs", "documentation": "docs",
    "scripts": "scripts", "script": "scripts",
    "tools": "tools", "tooling": "tools",
    "vendor": "vendor", "vendors": "vendor",
    "node_modules": "node_modules",
    "packages": "packages", "package": "packages",
    "modules": "modules",
    ".git": "git",
    ".vscode": "vscode",
    ".github": "github",
    ".idea": "idea",
    ".husky": "husky",
    ".next": "next",
    ".nuxt": "nuxt",
    ".svelte-kit": "svelte",
    "target": "target",
    "coverage": "coverage", "nyc_output": "coverage",
    "environment": "environment", "environments": "environment", "env": "environment",
    "secrets": "secrets", "secret": "secrets",
    "locales": "locales", "locale": "locales", "i18n": "locales",
    "translations": "locales", "translation": "locales",
    "database": "database", "db": "database",
    "migrations": "migrations", "migration": "migrations",
    "seeders": "seeders", "seeder": "seeders",
    "seeds": "seeders", "seed": "seeders",
    "prisma": "prisma", "drizzle": "database",
    "mocks": "mocks", "mock": "mocks", "__mocks__": "mocks",
    "examples": "examples", "example": "examples",
    "demo": "examples", "demos": "examples",
    "plugins": "plugins", "plugin": "plugins", "extensions": "plugins",
    "themes": "themes", "theme": "themes",
    "server": "server", "client": "client",
    "shared": "shared", "common": "common",
    "core": "core",
    "frontend": "frontend", "front": "frontend", "ui": "frontend",
    "backend": "backend", "back": "backend",
    "admin": "admin",
    "auth": "auth", "authentication": "auth",
    "constants": "constants", "const": "constants",
    "dto": "dto", "dtos": "dto",
    "entity": "entity", "entities": "entity",
    "repository": "repository", "repositories": "repository",
    "repo": "repository", "repos": "repository",
    ".circleci": "ci", ".gitlab": "ci",
    "docker": "docker",
    "logs": "logs", "log": "logs",
    "temp": "temp", "tmp": "temp",
    "cache": "cache", ".cache": "cache",
    "downloads": "downloads", "download": "downloads",
    "uploads": "uploads", "upload": "uploads",
    "video": "video", "videos": "video",
    "audio": "audio", "audios": "audio", "sounds": "audio", "music": "audio",
}

folder_names: dict[str, str] = {}
folder_names_expanded: dict[str, str] = {}
for alias, key in FOLDER_ALIASES.items():
    icon_key = f"folder_{key}"
    if icon_key in ICONS:
        folder_names[alias] = icon_key
        folder_names_expanded[alias] = f"{icon_key}_open"

THEME["folderNames"] = folder_names
THEME["folderNamesExpanded"] = folder_names_expanded


# --------------------------------------------------------------------------- #
# Write everything out
# --------------------------------------------------------------------------- #
ROOT = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(ROOT, "icons")


def write_all() -> tuple[int, int]:
    # Wipe stale SVGs before regenerating so renames don't leave orphans behind.
    if os.path.isdir(ICONS_DIR):
        for name in os.listdir(ICONS_DIR):
            if name.endswith(".svg"):
                os.remove(os.path.join(ICONS_DIR, name))
    os.makedirs(ICONS_DIR, exist_ok=True)

    for name, content in ICONS.items():
        with open(os.path.join(ICONS_DIR, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(content)

    theme_path = os.path.join(ROOT, "lusitania-icons-theme.json")
    with open(theme_path, "w", encoding="utf-8") as f:
        json.dump(THEME, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return len(ICONS), len(THEME["fileExtensions"])


if __name__ == "__main__":
    n_icons, n_ext = write_all()
    print(f"Wrote {n_icons} icons")
    print(f"  file extensions: {len(THEME['fileExtensions'])}")
    print(f"  file names:      {len(THEME['fileNames'])}")
    print(f"  folder names:    {len(THEME['folderNames'])}")
    print(f"  language IDs:    {len(THEME['languageIds'])}")
