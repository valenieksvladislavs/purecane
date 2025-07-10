import os
from bs4 import BeautifulSoup


def is_external(href):
    if not href:
        return False
    href = href.strip()
    return (
        href.startswith("http://")
        or href.startswith("https://")
        or href.startswith("//")
    )


def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    soup = BeautifulSoup(content, "html.parser")
    changed = False
    for a in soup.find_all("a", href=True):
        if is_external(a["href"]):
            a["href"] = "#"
            changed = True
    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"Updated: {file_path}")


def find_html_files(root="."):
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".html"):
                yield os.path.join(dirpath, filename)


if __name__ == "__main__":
    for file_path in find_html_files("."):
        process_file(file_path)
