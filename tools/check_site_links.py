#!/usr/bin/env python3
"""Check local links and fragments in a built static-site directory."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.anchors: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.anchors.add(values["id"])
        if tag == "a" and values.get("name"):
            self.anchors.add(values["name"])
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.references.append(values[attribute])


def parse(path: Path) -> Links:
    result = Links()
    result.feed(path.read_text(encoding="utf-8", errors="replace"))
    return result


def target_path(site: Path, source: Path, url_path: str) -> Path:
    decoded = unquote(url_path)
    candidate = site / decoded.lstrip("/") if decoded.startswith("/") else source.parent / decoded
    if decoded.endswith("/") or candidate.is_dir():
        candidate /= "index.html"
    return candidate.resolve()


def check(site: Path) -> None:
    site = site.resolve()
    documents = {path.resolve(): parse(path) for path in site.rglob("*.html")}
    failures: list[str] = []
    for source, document in documents.items():
        for reference in document.references:
            if "__REPOSITORY_URL__" in reference or "__PAGES_URL__" in reference:
                failures.append(f"{source.relative_to(site)}: unresolved placeholder {reference}")
                continue
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or reference.startswith(("mailto:", "data:", "javascript:")):
                continue
            target = target_path(site, source, parsed.path) if parsed.path else source
            if not target.exists():
                failures.append(f"{source.relative_to(site)}: missing {reference}")
                continue
            if parsed.fragment and target.suffix.lower() in {".html", ".htm"}:
                target_document = documents.get(target) or parse(target)
                if unquote(parsed.fragment) not in target_document.anchors:
                    failures.append(
                        f"{source.relative_to(site)}: missing fragment {reference}"
                    )
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"checked {len(documents)} HTML files: local links and fragments resolved")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path)
    check(parser.parse_args().site)


if __name__ == "__main__":
    main()
