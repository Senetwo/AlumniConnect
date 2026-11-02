"""Generate src/styles/dark.css from the light stylesheets.

The app's CSS uses hardcoded light colours in thousands of rules, so instead of
rewriting each one this script reads every stylesheet in cascade order and emits a
dark override for each rule that sets a light surface, text or border colour. Brand
crimson and the deliberately dark hero panels are kept as they are.

Run from the frontend folder after changing any stylesheet:

    python scripts/generate_dark_theme.py
"""
import colorsys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src"
SOURCES = [
    "index.css", "App.css", "styles/design-system.css", "styles/landing.css",
    "styles/register.css", "styles/login.css", "styles/community.css", "styles/mentors.css",
    "styles/content.css", "styles/chats.css", "styles/dashboard.css", "styles/admin.css", "styles/vibrance.css",
]
OUTPUT = ROOT / "styles" / "dark.css"
SCOPE = ':root[data-theme="dark"]'

# Panels that are dark in both themes keep their dark backgrounds.
KEEP_DARK = (
    "lp-hero", "lp-footer", "lp-band", "lp-cta", "auth-showcase", "register-aside",
    "cm-me-cover", "mp-cover", "pf-hero-cover", "knowledge-hero", "workspace-hero",
    "hero-image", "lp-hero-shade", "stripe",
)

SURFACE, SUNKEN, RAISED, DARK_ELEMENT = "#1d1d21", "#26262b", "#2f2f35", "#3b3b42"
TEXT, MUTED = "#ececef", "#a7a7ae"
BORDER_LIGHT, BORDER_DARK = "#37373d", "#6b6b73"
ACCENT_TINT = "rgba(226, 7, 20, 0.16)"

# Variables that hold the brand cod gray / near-black. Where they set text, a surface or a
# border the dark theme needs the matching dark-theme colour, so they are resolved here.
DARK_VARIABLES = re.compile(r"var\(--(?:navy|navy-light|cm-gray|reg-gray|auth-gray|green)\)")

COLOUR = re.compile(r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgba?\([^)]*\)|\b(?:white|black)\b")


def parse_colour(token):
    token = token.strip().lower()
    if token == "white":
        return 255, 255, 255, 1.0
    if token == "black":
        return 0, 0, 0, 1.0
    if token.startswith("#"):
        h = token[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        alpha = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha
    nums = re.findall(r"[\d.]+", token)
    r, g, b = (float(n) for n in nums[:3])
    return r, g, b, float(nums[3]) if len(nums) > 3 else 1.0


def hls(r, g, b):
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)


def is_brand_red(h, s, l):
    return (h < 0.04 or h > 0.96) and s > 0.6 and 0.25 < l < 0.75


def rgba_of(hex_colour, alpha):
    h = hex_colour.lstrip("#")
    return f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, {alpha:g})"


def map_background(token, keep_dark):
    r, g, b, a = parse_colour(token)
    h, l, s = hls(r, g, b)
    if is_brand_red(h, s, l):
        return None
    if (h < 0.06 or h > 0.94) and l > 0.88 and s > 0.3:
        return ACCENT_TINT
    if l >= 0.82:
        if a < 1:
            return rgba_of(SURFACE, a)
        return SURFACE if l >= 0.985 else SUNKEN if l >= 0.94 else RAISED
    if l < 0.22 and a >= 1 and not keep_dark:
        return DARK_ELEMENT
    return None


def map_text(token):
    r, g, b, a = parse_colour(token)
    h, l, s = hls(r, g, b)
    if is_brand_red(h, s, l) or a < 1:
        return None
    if l <= 0.42:
        return TEXT
    if l <= 0.68:
        return MUTED
    return None


def map_border(token):
    r, g, b, a = parse_colour(token)
    h, l, s = hls(r, g, b)
    if is_brand_red(h, s, l) or a < 1:
        return None
    if l >= 0.6:
        return BORDER_LIGHT
    if l < 0.3:
        return BORDER_DARK
    return None


def category(prop):
    if prop in ("color", "caret-color", "fill", "stroke", "text-decoration-color"):
        return "text"
    if prop in ("background", "background-color"):
        return "background"
    if prop == "border" or re.fullmatch(r"border(-(top|right|bottom|left))?(-color)?", prop):
        return "border"
    return None


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def split_top_level(text, sep):
    parts, depth, current = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return parts


def parse_blocks(css):
    """Yield (header, body) pairs for the top-level blocks of a stylesheet."""
    i, n = 0, len(css)
    while i < n:
        start = i
        while i < n and css[i] not in "{;":
            i += 1
        if i >= n:
            return
        if css[i] == ";":
            i += 1
            continue
        header = css[start:i].strip()
        depth, j = 1, i + 1
        while j < n and depth:
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        yield header, css[i + 1:j - 1]
        i = j


def dark_declarations(selector, body):
    keep_dark = any(name in selector for name in KEEP_DARK)
    out = []
    for decl in split_top_level(body, ";"):
        if ":" not in decl:
            continue
        prop, _, value = decl.partition(":")
        prop, value = prop.strip().lower(), value.strip()
        kind = category(prop)
        if not kind or "gradient" in value or "url(" in value:
            continue
        important = " !important" if "!important" in value else ""
        raw = DARK_VARIABLES.sub("#1c1c1c", value.replace("!important", "").strip())
        if "var(" in raw and kind != "border":
            continue
        tokens = [m.group(0) for m in COLOUR.finditer(raw)]
        if not tokens:
            continue
        changed = raw
        touched = False
        for token in dict.fromkeys(tokens):
            if kind == "background":
                mapped = map_background(token, keep_dark)
            elif kind == "text":
                mapped = map_text(token)
            else:
                mapped = map_border(token)
            if mapped:
                changed = changed.replace(token, mapped)
                touched = True
        if touched:
            out.append(f"  {prop}: {changed}{important};")
    return out


def prefix_selector(selector):
    selector = selector.strip()
    if selector.startswith(":root"):
        return selector.replace(":root", SCOPE, 1)
    if selector.startswith("html"):
        return 'html[data-theme="dark"]' + selector[4:]
    if selector.startswith("body"):
        return f"{SCOPE} body" + selector[4:]
    return f"{SCOPE} {selector}"


def convert(css):
    chunks = []
    for header, body in parse_blocks(css):
        if header.startswith("@media") or header.startswith("@supports"):
            inner = convert(body)
            if inner.strip():
                chunks.append(f"{header} {{\n{inner}}}\n")
            continue
        if header.startswith("@") or header == "*" or not header:
            continue
        declarations = dark_declarations(header, body)
        if not declarations:
            continue
        selectors = ",\n".join(prefix_selector(s) for s in split_top_level(header, ",") if s.strip())
        chunks.append(f"{selectors} {{\n" + "\n".join(declarations) + "\n}\n")
    return "\n".join(chunks)


TOKENS = f"""{SCOPE} {{
  color-scheme: dark;
  --cream: #121214; --background: #121214; --color-bg: #121214;
  --white: {SURFACE}; --surface: {SURFACE}; --color-surface: {SURFACE};
  --soft: {SUNKEN}; --surface-muted: {SUNKEN}; --social-bg: {SUNKEN}; --color-surface-sunken: {SUNKEN};
  --text: {TEXT}; --color-text: {TEXT};
  --muted: {MUTED}; --text-secondary: {MUTED}; --color-text-muted: {MUTED}; --color-text-subtle: #8b8b93;
  --border: #2f2f35; --color-border: #2f2f35; --border-strong: #45454c; --color-border-strong: #45454c;
  --red-soft: {ACCENT_TINT}; --accent-bg: {ACCENT_TINT};
  --status-pending-bg: #3a3320; --status-danger-bg: #3a1d20; --status-success-bg: {SUNKEN}; --status-info-bg: {SUNKEN};
  --status-success-fg: {TEXT}; --status-info-fg: {TEXT};
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.4); --shadow-md: 0 12px 32px rgba(0, 0, 0, 0.5);
}}
"""

EXTRAS = f"""
/* Hand-written dark rules for things the generator cannot infer. */
{SCOPE} body {{ background: #121214; color: {TEXT}; }}
{SCOPE} input::placeholder, {SCOPE} textarea::placeholder {{ color: #7c7c85; }}
{SCOPE} input, {SCOPE} select, {SCOPE} textarea {{ background-color: {SURFACE}; color: {TEXT}; border-color: #45454c; }}
{SCOPE} select option {{ background: {SURFACE}; color: {TEXT}; }}
{SCOPE} .auth-page input:-webkit-autofill,
{SCOPE} .auth-page input:-webkit-autofill:hover,
{SCOPE} .auth-page input:-webkit-autofill:focus {{
  -webkit-box-shadow: 0 0 0 1000px {SURFACE} inset;
  -webkit-text-fill-color: {TEXT};
  caret-color: {TEXT};
}}
{SCOPE} .pg-skeleton, {SCOPE} .cm-skeleton, {SCOPE} .mp-skeleton {{ background: linear-gradient(90deg, #232328, #2b2b31, #232328); }}
{SCOPE} .workspace-switch-link::before {{ background: #22c55e; }}
{SCOPE} {{
  --tint-red-bg: rgba(226, 7, 20, 0.2);    --tint-red-fg: #ff8a90;
  --tint-green-bg: rgba(34, 197, 94, 0.18); --tint-green-fg: #6ee79a;
  --tint-amber-bg: rgba(245, 158, 11, 0.18); --tint-amber-fg: #fbbf5a;
  --tint-blue-bg: rgba(96, 140, 255, 0.2);  --tint-blue-fg: #9db9ff;
  --tint-violet-bg: rgba(167, 122, 255, 0.2); --tint-violet-fg: #c4a8ff;
}}
{SCOPE} .pg-stat-icon, {SCOPE} .admin-metric-icon, {SCOPE} .admin-total-icon, {SCOPE} .admin-ops-summary-icon,
{SCOPE} .admin-activity-icon, {SCOPE} .admin-attention-row-icon, {SCOPE} .knowledge-resource-card .knowledge-resource-icon {{ background: var(--tint-red-bg); color: var(--tint-red-fg); }}
{SCOPE} .pg-stats .pg-stat:nth-child(2) .pg-stat-icon, {SCOPE} .admin-metric-grid .admin-metric-card:nth-child(2) .admin-metric-icon, {SCOPE} .admin-activity-card:nth-child(2) .admin-activity-icon {{ background: var(--tint-green-bg); color: var(--tint-green-fg); }}
{SCOPE} .pg-stats .pg-stat:nth-child(3) .pg-stat-icon, {SCOPE} .admin-ops-summary article:nth-child(2) .admin-ops-summary-icon {{ background: var(--tint-amber-bg); color: var(--tint-amber-fg); }}
{SCOPE} .admin-metric-grid .admin-metric-card:nth-child(4) .admin-metric-icon {{ background: var(--tint-amber-bg); color: var(--tint-amber-fg); }}
{SCOPE} .pg-stats .pg-stat:nth-child(4) .pg-stat-icon, {SCOPE} .admin-ops-summary article:nth-child(3) .admin-ops-summary-icon {{ background: var(--tint-blue-bg); color: var(--tint-blue-fg); }}
{SCOPE} .admin-metric-grid .admin-metric-card:nth-child(3) .admin-metric-icon, {SCOPE} .admin-activity-card:nth-child(3) .admin-activity-icon {{ background: var(--tint-violet-bg); color: var(--tint-violet-fg); }}
{SCOPE} .pg-stat.is-accent .pg-stat-icon {{ background: var(--gradient-brand); color: #fff; }}
{SCOPE} .pg-tabs button.is-active, {SCOPE} .admin-ops-tabs button.is-selected {{ background: var(--color-accent); border-color: var(--color-accent); color: #fff; }}
{SCOPE} .lp-btn-light {{ background: #fff; color: #1c1c1c; }}
{SCOPE} .lp-btn-light:hover {{ background: #f3f3f3; color: #1c1c1c; }}
{SCOPE} body {{ background-image: radial-gradient(900px 420px at 100% -80px, rgba(226, 7, 20, 0.16), transparent 70%), radial-gradient(700px 360px at -10% 0, rgba(34, 197, 94, 0.07), transparent 70%); }}
{SCOPE} .admin-status-pill.status-active,
{SCOPE} .admin-status-pill.status-accepted,
{SCOPE} .admin-verification.verified {{ background: rgba(34, 197, 94, 0.16); color: #6ee79a; }}
{SCOPE} .admin-status-pill.status-active i,
{SCOPE} .admin-status-pill.status-accepted i,
{SCOPE} .admin-verification.verified i {{ background: #22c55e; }}
{SCOPE} .admin-status-pill.status-suspended,
{SCOPE} .admin-status-pill.status-declined {{ background: rgba(226, 7, 20, 0.2); color: #ff8a90; }}
{SCOPE} .admin-role-pill.role-mentor {{ background: rgba(96, 140, 255, 0.18); color: #9db9ff; }}
{SCOPE} .admin-role-pill.role-mentee {{ background: rgba(167, 122, 255, 0.18); color: #c4a8ff; }}
{SCOPE} .btn-primary,
{SCOPE} .app-content-page .btn-primary,
{SCOPE} .cm-page .btn-primary,
{SCOPE} .admin-community .btn-primary,
{SCOPE} .admin-knowledge-page button.bg-red-700,
{SCOPE} .admin-knowledge-page form button.btn {{ border-color: #e20714; background: #e20714; color: #fff; }}
{SCOPE} .btn-primary:hover:not(:disabled),
{SCOPE} .app-content-page .btn-primary:hover:not(:disabled),
{SCOPE} .cm-page .btn-primary:hover:not(:disabled),
{SCOPE} .admin-community .btn-primary:hover:not(:disabled) {{ border-color: #b8050f; background: #b8050f; }}
{SCOPE} .match-best {{ color: #fff; }}
{SCOPE} select:not([multiple]) {{
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23a7a7ae' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E") !important;
}}
{SCOPE} .brand-name {{ color: {TEXT}; }}
{SCOPE} .landing-page .lp-hero .brand-name,
{SCOPE} .lp-footer .brand-name {{ color: #fff; }}
"""


def main():
    parts = ["/* Generated by scripts/generate_dark_theme.py. Do not edit by hand. */\n", TOKENS]
    for name in SOURCES:
        css = strip_comments((ROOT / name).read_text(encoding="utf-8"))
        parts.append(f"/* from {name} */\n" + convert(css))
    parts.append(EXTRAS)
    OUTPUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
