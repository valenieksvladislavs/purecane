import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

# Папки для ресурсов
RESOURCE_DIRS = {
    "fonts": [".woff", ".woff2", ".ttf", ".otf", ".eot"],
    "css": [".css"],
    "js": [".js"],
    "images": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"],
}


def get_resource_dir(url):
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    for folder, exts in RESOURCE_DIRS.items():
        if ext in exts:
            return folder
    return "other"


def download_resource(url, folder):
    os.makedirs(folder, exist_ok=True)
    filename = os.path.basename(unquote(urlparse(url).path))
    local_path = os.path.join(folder, filename)
    if not os.path.exists(local_path):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                "Referer": "https://purecane.com/"
            }
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)
            print(f"Downloaded: {url} -> {local_path}")
        except Exception as e:
            print(f"Failed: {url} ({e})")
    return local_path


def replace_links_in_html(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    changed = False

    # <link>
    for tag in soup.find_all("link", href=True):
        if tag.get('rel') and tag['rel'][0] in ['preconnect', 'dns-prefetch']:
            continue
        url = normalize_url(tag['href'])
        if url.startswith("http"):
            folder = get_resource_dir(url)
            local_path = download_resource(url, folder)
            tag["href"] = make_absolute_path(local_path)
            changed = True

    # <script>
    for tag in soup.find_all("script", src=True):
        url = normalize_url(tag['src'])
        if url.startswith("http"):
            folder = get_resource_dir(url)
            local_path = download_resource(url, folder)
            tag["src"] = make_absolute_path(local_path)
            changed = True

    # <img>, <iframe>, <video>
    for tag in soup.find_all(['img', 'iframe', 'video']):
        for attr in ['src', 'data-src']:
            if tag.has_attr(attr):
                url = normalize_url(tag[attr])
                if url.startswith('http'):
                    folder = get_resource_dir(url)
                    local_path = download_resource(url, folder)
                    tag[attr] = make_absolute_path(local_path)
                    changed = True

    # <source>
    for tag in soup.find_all('source'):
        for attr in ['src', 'data-src', 'srcset', 'data-srcset']:
            if tag.has_attr(attr):
                urls = [u.strip().split(' ')[0] for u in tag[attr].split(',')]
                new_urls = []
                for url in urls:
                    url = normalize_url(url)
                    if url.startswith('http'):
                        folder = get_resource_dir(url)
                        local_path = download_resource(url, folder)
                        new_urls.append(make_absolute_path(local_path))
                    else:
                        new_urls.append(url)
                tag[attr] = ', '.join(new_urls)
                changed = True

    # <div data-bg="...">
    for tag in soup.find_all(attrs={"data-bg": True}):
        url = normalize_url(tag['data-bg'])
        if url.startswith('http'):
            folder = get_resource_dir(url)
            local_path = download_resource(url, folder)
            tag['data-bg'] = make_absolute_path(local_path)
            changed = True

    # @font-face в <style>
    for style in soup.find_all("style"):
        css = style.string
        if not css:
            continue
        urls = re.findall(r"url\(([^)]+)\)", css)
        for url in urls:
            url = url.strip("'\"")
            if url.startswith("http"):
                folder = get_resource_dir(url)
                local_path = download_resource(url, folder)
                css = css.replace(url, make_absolute_path(local_path))
                changed = True
        style.string = css

    if changed:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"Updated: {html_path}")


def find_html_files(root="."):
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".html"):
                yield os.path.join(dirpath, filename)


def normalize_url(url):
    if url.startswith('//'):
        return 'https:' + url
    return url


def make_absolute_path(local_path):
    return '/' + os.path.relpath(local_path, start='.').replace(os.sep, '/')


if __name__ == "__main__":
    for html_file in find_html_files("."):
        replace_links_in_html(html_file)
