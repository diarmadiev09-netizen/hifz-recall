"""Dictionary entries (lemmas) of the Quran, ranked by how many words they cover.

Shared by build_grammar.py, and runnable to print a slice for translating:
    python src/lemmas.py 1 350      # ranks 1-350 with their commonest English glosses
Ranks are stable: entries sort by frequency, then by their corpus key.
"""
import collections, json, os, sys

SRC = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(os.path.dirname(SRC), "grammar")
BW = dict(zip("'|><&}AbptvjHxd*rzs$SDTZEg_fqklmnhwYyFNKaui~o^#`{",
              "ءآأإؤئابةتثجحخدذرزسشصضطظعغـ"
              "فقكلمنهوىيًٌٍَُِّْٰٓٔٱ"))  # Buckwalter -> Arabic
def ar(bw): return "".join(BW.get(c, "") for c in bw)


def load():
    """Returns (key per word location, ranked entries). An entry is (key, Arabic form, POS tag, word count)."""
    word_key, info = {}, {}
    for line in open(os.path.join(G, "quranic-corpus-morphology-0.4.txt"), encoding="utf8"):
        if line.startswith(("#", "LOCATION")) or not line.strip(): continue
        loc, form, tag, feats = line.rstrip("\n").split("\t")
        s, v, w, _ = map(int, loc.strip("()").split(":"))
        parts = feats.split("|")
        if "STEM" not in parts or (s, v, w) in word_key: continue
        lem = next((p[4:] for p in parts if p.startswith("LEM:")), None)
        key = lem or "FORM:" + form
        word_key[(s, v, w)] = key
        info.setdefault(key, (ar(lem or form), tag))
    count = collections.Counter(word_key.values())
    ranked = [(k, info[k][0], info[k][1], n) for k, n in sorted(count.items(), key=lambda kv: (-kv[1], kv[0]))]
    return word_key, ranked


if __name__ == "__main__":
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    word_key, ranked = load()
    quran = json.load(open(os.path.join(SRC, "quran.json"), encoding="utf8"))["surahs"]
    glosses = collections.defaultdict(collections.Counter)
    for sid, verses in quran.items():
        for v in verses:
            for i, g in enumerate(v["g"]):
                glosses[word_key[(int(sid), v["n"], i + 1)]][g.strip().lower()] += 1
    for rank in range(lo, hi + 1):
        key, arabic, tag, n = ranked[rank - 1]
        top = "; ".join(g[:26] for g, _ in glosses[key].most_common(2))
        print(f"{rank}|{arabic}|{tag}|{top}")
