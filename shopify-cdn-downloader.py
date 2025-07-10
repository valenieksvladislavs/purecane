import os
import re
import requests
from urllib.parse import urlparse, unquote

# Расширения и папки для ресурсов
RESOURCE_MAP = {
    "images": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"],
    "fonts": [".woff", ".woff2", ".ttf", ".otf", ".eot"],
    "js": [".js"],
    "css": [".css", ".scss"],
}


def get_resource_folder(url):
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    for folder, exts in RESOURCE_MAP.items():
        if ext in exts:
            return folder
    return "assets"


def download_resource(url, folder):
    os.makedirs(folder, exist_ok=True)
    filename = os.path.basename(unquote(urlparse(url).path))
    local_path = os.path.join(folder, filename)
    if not os.path.exists(local_path):
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://purecane.com/"}
        try:
            r = requests.get(
                url if url.startswith("http") else "https:" + url,
                headers=headers,
                timeout=20,
            )
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)
            print(f"Downloaded: {url} -> {local_path}")
        except Exception as e:
            print(f"Failed: {url} ({e})")
    return "/" + local_path.replace(os.sep, "/")


def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    cdn_pattern = r'(?:https?:)?//cdn\.shopify\.com[^\s"\'\)\]]+'
    matches = set(re.findall(cdn_pattern, content))
    changed = False

    for match in matches:
        url = match if match.startswith('http') else 'https:' + match
        folder = get_resource_folder(url)
        local_path = download_resource(url, folder)
        # Проверяем, существует ли файл локально
        if os.path.exists(local_path.lstrip('/')):
            content_new = content.replace(match, local_path)
            print(match, local_path)
            if content_new != content:
                changed = True
                content = content_new
        else:
            print(f"Skip replace: {url} (file not downloaded)")

    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")


def find_files(root=".", extensions=(".html", ".css", ".js")):
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(extensions):
                yield os.path.join(dirpath, filename)


if __name__ == "__main__":
    for file_path in find_files("."):
        process_file(file_path)
