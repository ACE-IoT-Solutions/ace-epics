"""Check local targets and fragments in a built documentation site."""

import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Links(HTMLParser):
    """Collect anchor targets and document IDs."""

    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "a" and "href" in attributes:
            self.links.append(attributes["href"])


def main():
    """Validate generated HTML navigation without fetching external sites."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", nargs="?", type=Path, default=Path("site"))
    root = parser.parse_args().site.resolve()
    pages = {}
    for path in root.rglob("*.html"):
        links = Links()
        links.feed(path.read_text(encoding="utf-8"))
        pages[path] = links
    errors = []
    for path, data in pages.items():
        for href in data.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            relative = unquote(url.path)
            target = (
                (root / relative.lstrip("/")).resolve()
                if relative.startswith("/")
                else (path.parent / relative).resolve()
                if relative
                else path
            )
            if target.is_dir():
                target /= "index.html"
            if not target.exists():
                errors.append(f"{path.relative_to(root)}: missing target {href}")
            elif (
                url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids
            ):
                errors.append(f"{path.relative_to(root)}: missing anchor {href}")
    for error in errors:
        print(error)
    print(f"Checked {len(pages)} pages; {len(errors)} broken local links")
    return int(bool(errors) or not pages)


if __name__ == "__main__":
    raise SystemExit(main())
