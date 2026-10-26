"""Build the self-contained report.html and slides.html from docs/*_src.html.

Inlines every screenshot as a data URI, links reveal.js from a CDN (with an embedded offline copy), and drops in the latest
test results, so both files open by double-clicking on any computer.

Run from the project folder:
    python scripts/build_docs.py
"""

import base64
import html
import mimetypes
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DOCS = PROJECT / "docs"


def inline_images(page: str) -> str:
    def repl(m):
        path = DOCS / m.group(2)
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        data = base64.b64encode(path.read_bytes()).decode()
        return f'{m.group(1)}"data:{mime};base64,{data}"'
    return re.sub(r'(<img[^>]*?\bsrc=)"((?:screenshots)/[^"]+)"', repl, page)


def test_results() -> str:
    path = PROJECT / "output" / "test_results.txt"
    text = html.escape(path.read_text().strip()) if path.exists() else "(run the tests to fill this in)"
    return text.replace("PASSED", '<span class="ok">PASSED</span>')


def main():
    report = (DOCS / "report_src.html").read_text()
    report = report.replace("{{TEST_RESULTS}}", test_results())
    (PROJECT / "report.html").write_text(inline_images(report))

    diagram = re.search(r'<svg class="diagram".*?</svg>', report, re.S).group(0)
    slides = (DOCS / "slides_src.html").read_text()
    vendor = DOCS / "vendor" / "reveal"
    slides = (slides.replace("{{DIAGRAM}}", diagram)
                    .replace("{{REVEAL_CSS}}", (vendor / "reveal.css").read_text())
                    .replace("{{REVEAL_JS}}", (vendor / "reveal.js").read_text()))
    (PROJECT / "slides.html").write_text(inline_images(slides))

    for name in ("report.html", "slides.html"):
        size = (PROJECT / name).stat().st_size
        print(f"wrote {name} ({size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
