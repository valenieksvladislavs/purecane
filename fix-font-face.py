import re
from bs4 import BeautifulSoup


def fix_font_face_blocks(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    changed = False

    style_pattern = r"<style[^>]*>(.*?)</style>"
    style_matches = re.findall(style_pattern, content, re.DOTALL)

    for style_content in style_matches:
        font_face_pattern = r"@font-face\s*\{[^}]*\}"
        font_face_blocks = re.findall(font_face_pattern, style_content, re.DOTALL)

        font_families = {}
        for block in font_face_blocks:
            family_match = re.search(r"font-family:\s*([^;]+);", block)
            if family_match:
                family = family_match.group(1).strip().strip("\"'")

                weight_match = re.search(r"font-weight:\s*([^;]+);", block)
                if weight_match:
                    weight = weight_match.group(1).strip()

                    if "/" in weight or "." in weight:
                        if family not in font_families:
                            font_families[family] = []
                        font_families[family].append(("error", block))
                    else:
                        if family not in font_families:
                            font_families[family] = []
                        font_families[family].append(("correct", block))

        for family, blocks in font_families.items():
            error_blocks = [b for t, b in blocks if t == "error"]
            correct_blocks = [b for t, b in blocks if t == "correct"]

            if error_blocks and correct_blocks:
                for error_block in error_blocks:
                    content = content.replace(error_block, "")
                    changed = True
                    print(f"Removed error font-face block for {family} in {html_path}")

    if changed:
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {html_path}")


def find_html_files(root="."):
    import os

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".html"):
                yield os.path.join(dirpath, filename)


if __name__ == "__main__":
    for html_file in find_html_files("."):
        fix_font_face_blocks(html_file)
