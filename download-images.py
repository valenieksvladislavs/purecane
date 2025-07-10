import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def download_image(url, folder="images"):
    ensure_dir(folder)
    if url.startswith("//"):
        url = "https:" + url
    filename = os.path.basename(unquote(urlparse(url).path))
    local_path = os.path.join(folder, filename)
    if not os.path.exists(local_path):
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://purecane.com/"}
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(r.content)
            print(f"Downloaded: {url} -> {local_path}")
        except Exception as e:
            print(f"Failed: {url} ({e})")
    return "/" + local_path.replace(os.sep, "/")


def process_html_file(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    changed = False

    for img in soup.find_all("img"):
        if (
            img.has_attr("data-src")
            and "{width}x" in img["data-src"]
            and img.has_attr("data-widths")
        ):
            try:
                widths = [int(w) for w in re.findall(r"\d+", img["data-widths"])]
                max_width = max(widths)
                url = img["data-src"].replace("{width}", str(max_width))
                local_path = download_image(url)
                img["src"] = local_path
                del img["data-src"]
                if img.has_attr("data-widths"):
                    del img["data-widths"]
                changed = True
            except Exception as e:
                print(f"Error processing data-src: {e}")

        if img.has_attr("data-srcset"):
            srcset = img["data-srcset"]
            candidates = re.findall(r"([^\s,]+)\s+(\d+)w", srcset)
            if candidates:
                max_url, _ = max(candidates, key=lambda x: int(x[1]))
                local_path = download_image(max_url)
                img["src"] = local_path
                del img["data-srcset"]
                changed = True

        if img.has_attr("srcset"):
            srcset = img["srcset"]
            candidates = re.findall(r"([^\s,]+)\s+(\d+)w", srcset)
            if candidates:
                max_url, _ = max(candidates, key=lambda x: int(x[1]))
                local_path = download_image(max_url)
                img["src"] = local_path
                del img["srcset"]
                changed = True

        if img.has_attr("data-src") and "{width}" not in img["data-src"]:
            url = img["data-src"]
            local_path = download_image(url)
            img["src"] = local_path
            del img["data-src"]
            changed = True

        if img.has_attr("class"):
            classes = [c for c in img["class"] if c != "lazyload"]
            if len(classes) != len(img["class"]):
                img["class"] = classes
                changed = True

        if not img.has_attr("loading") or img["loading"] != "lazy":
            img["loading"] = "lazy"
            changed = True

    for tag in soup.find_all(attrs={"data-bg": True}):
        url = tag["data-bg"]
        local_path = download_image(url)
        tag["style"] = f"background-image: url('{local_path}');"
        del tag["data-bg"]
        changed = True

    if changed:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
        print(f"Updated: {html_path}")


def find_html_files(root="."):
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".html"):
                yield os.path.join(dirpath, filename)


if __name__ == "__main__":
    for html_file in find_html_files("."):
        process_html_file(html_file)
