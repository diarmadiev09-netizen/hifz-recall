import json, re, sys, os
src, out = sys.argv[1], sys.argv[2]
CYR = "А-ЯЁӘҒҚҢӨҰҮҺІа-яёәғқңөұүһі"
def ws(t): return re.sub(r"[ \t\xa0‏‎]+", " ", t).strip()
def glue(t): return re.sub(r"\s+(?=[ۖ-ۭ])", "", ws(t))  # stop/sajdah marks sit on the word
def en(t): return ws(re.sub(r"<[^>]+>", "", re.sub(r"<sup[^>]*>.*?</sup>", "", t)))
def kk(t):
    t = t.replace("\xa0", " ")
    # keep the translator's own /explanation/ notation: the source has unpaired slashes, so rewriting them corrupts verses
    t = ws(t)
    t = re.sub(r"\s+([.,;:!?»)\]])", r"\1", t)
    t = re.sub(r"([«(\[])\s+", r"\1", t)
    t = re.sub(r"([.,;:!?])(?=[" + CYR + "])", r"\1 ", t)
    return t
def ru(t): return ws(re.sub(r"<[^>]+>", "", t))
chapters = json.load(open(os.path.join(src, "chapters.json"), encoding="utf8"))
data, stats = {}, {"verses": 0, "words": 0, "kk_slash_left": 0, "empty": 0, "hizb": 0, "joins": 0}
for c in chapters:
    vs = []
    for v in json.load(open(os.path.join(src, f"raw{c['id']}.json"), encoding="utf8")):
        words = [w for w in v["words"] if w["char_type_name"] == "word"]
        tr = {t["resource_id"]: t["text"] for t in v["translations"]}
        W = [glue(w["text_qpc_hafs"]) for w in words]
        h = 0
        if W[0].startswith("۞"):
            h = 1; W[0] = W[0][1:].strip()
        assert all(W), v["verse_key"]
        ref = glue(re.sub(r"[\s\xa0]*[٠-٩]+$", "", v["text_qpc_hafs"]).replace("۞", "")).strip()
        pos, J = 0, []          # J[i] = 1 when word i joins the next with no space (one mushaf word)
        for i, w in enumerate(W):
            assert ref.startswith(w, pos), (v["verse_key"], i, w, ref[pos:pos+20])
            pos += len(w)
            if i < len(W) - 1:
                if ref[pos:pos+1] == " ": pos += 1; J.append(0)
                else: J.append(1); stats["joins"] += 1
        assert pos == len(ref), v["verse_key"]
        row = {"n": v["verse_number"], "w": W,
               "g": [ws((w.get("translation") or {}).get("text") or "") for w in words],
               "r": [ws((w.get("transliteration") or {}).get("text") or "") for w in words],
               "en": en(tr[20]), "ru": ru(tr[45]), "kk": kk(tr[113]),
               "a": (v.get("audio") or {}).get("url", ""), "pg": v["page_number"], "j": v["juz_number"]}
        if any(J): row["J"] = J
        if h: row["h"] = 1; stats["hizb"] += 1
        for k in ("en", "ru", "kk"):
            if not row[k]: stats["empty"] += 1
        if "/" in row["kk"]: stats["kk_slash_left"] += 1
        stats["verses"] += 1; stats["words"] += len(W)
        vs.append(row)
    assert len(vs) == c["c"] and [x["n"] for x in vs] == list(range(1, c["c"] + 1)), c["id"]
    data[c["id"]] = vs
json.dump({"chapters": chapters, "surahs": data}, open(out, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
print(stats, os.path.getsize(out))
