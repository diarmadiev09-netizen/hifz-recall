"""Build Hifz Recall from app.html, quran.json and the KFGQPC Hafs font.

Outputs
  docs/   installable offline web app (served by GitHub Pages): index.html, sw.js, manifest
  dist/Hifz-Recall.html   one-file offline copy to open from a phone's storage
  dist/artifact.html      body-only copy for the claude.ai artifact
"""
import base64, hashlib, json, os, shutil

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
DOCS, DIST = os.path.join(ROOT, "docs"), os.path.join(ROOT, "dist")
ICONS = ["icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"]


def read(name, binary=False):
    with open(os.path.join(SRC, name), "rb" if binary else "r", **({} if binary else {"encoding": "utf8"})) as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write(text)


def data_tags():
    q = json.loads(read("quran.json"))

    def tag(id_, obj):
        s = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        return f'<script type="application/json" id="{id_}">{s}</script>'

    parts = [tag("q-chapters", q["chapters"])]
    for sid, verses in q["surahs"].items():
        for v in verses:
            v.pop("a", None)  # the audio path is derived from the sūrah and āyah numbers
        parts.append(tag(f"q-{sid}", verses))
    return "\n".join(parts)


def bundle(pwa):
    body = read("app.html")
    body = body.replace("/*FONT_HAFS*/", base64.b64encode(read("fonts/hafs.woff2", True)).decode())
    body = body.replace("/*DATA*/", data_tags())
    assert "/*FONT_HAFS*/" not in body and "/*DATA*/" not in body
    if pwa:
        assert "const PWA = false;" in body
        body = body.replace("const PWA = false;", "const PWA = true;", 1)
    return body


def standalone(body, extra_head=""):
    """Wrap the page in a full document, moving its <title> and <style> into <head>."""
    cut = body.index("</style>") + len("</style>")
    return ('<!doctype html>\n<html lang="kk"><head><meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
            '<meta name="color-scheme" content="light dark">\n'
            '<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">\n'
            '<meta name="theme-color" content="#162025" media="(prefers-color-scheme: dark)">\n'
            + extra_head + body[:cut] + "\n</head><body>" + body[cut:] + "\n</body></html>\n")


PWA_HEAD = """<meta name="description" content="Memorise the Quran with active recall and spaced review. Kazakh, Russian and English.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png" type="image/png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Hifz Recall">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
"""

if __name__ == "__main__":
    plain = bundle(pwa=False)
    write(os.path.join(DIST, "Hifz-Recall.html"), standalone(plain))
    write(os.path.join(DIST, "artifact.html"), plain)

    index = standalone(bundle(pwa=True), PWA_HEAD)
    write(os.path.join(DOCS, "index.html"), index)
    shutil.copyfile(os.path.join(SRC, "manifest.webmanifest"), os.path.join(DOCS, "manifest.webmanifest"))
    h = hashlib.sha256(index.encode("utf8") + read("manifest.webmanifest").encode("utf8"))
    for icon in ICONS:
        p = os.path.join(DOCS, icon)
        if os.path.exists(p):
            h.update(open(p, "rb").read())
        else:
            print("missing icon:", icon)
    write(os.path.join(DOCS, "sw.js"), read("sw.js").replace("__VERSION__", h.hexdigest()[:12]))
    write(os.path.join(DOCS, ".nojekyll"), "")

    for p in (os.path.join(DOCS, "index.html"), os.path.join(DIST, "Hifz-Recall.html"), os.path.join(DIST, "artifact.html")):
        print(os.path.relpath(p, ROOT), round(os.path.getsize(p) / 1e6, 2), "MB")
