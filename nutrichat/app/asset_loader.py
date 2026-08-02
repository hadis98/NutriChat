from pathlib import Path


ASSETS_DIR = Path(__file__).resolve().parent / "assets"

CSS_FILES = (
    "styles/base.css",
    "styles/results.css",
    "styles/dashboard.css",
    "styles/responsive.css",
    "theme-light.css",
    "themes/dark/dark-base.css",
    "themes/dark/shell.css",
    "themes/dark/examples.css",
    "themes/dark/advanced.css",
    "themes/dark/results.css",
    "themes/dark/responsive.css",
)
CUSTOM_CSS = "\n\n".join(
    (ASSETS_DIR / filename).read_text(encoding="utf-8") for filename in CSS_FILES
)
APP_SHELL_SCRIPT = (ASSETS_DIR / "app-shell.js").read_text(encoding="utf-8")
CUSTOM_HEAD = f"<script>{APP_SHELL_SCRIPT}</script>"
SPINNER_HTML = (ASSETS_DIR / "spinner.html").read_text(encoding="utf-8")


def spinner_html(message: str) -> str:
    return SPINNER_HTML.replace("generating your answer...", message)
