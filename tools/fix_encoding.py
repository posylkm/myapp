from pathlib import Path

def convert_file(p: Path):
    raw = p.read_bytes()
    try:
        raw.decode("utf-8")
        print(f"OK (utf-8): {p}")
        return
    except UnicodeDecodeError as e:
        print(f"Converting {p} (error at pos {e.start}, byte {raw[e.start]:#x})")

    text = raw.decode("cp1252")  # Windows-1252
    # Optional: normalize fancy punctuation to ASCII
    replacements = {
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2018": "'", "\u2019": "'",  # single quotes
        "\u201c": '"', "\u201d": '"',  # double quotes
        "\u2026": "...",
        "\u00a0": " ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    p.write_text(text, encoding="utf-8")

root = Path("templates")
for p in root.rglob("*.html"):
    convert_file(p)
print("Done.")
