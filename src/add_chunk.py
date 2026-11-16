"""Append grammar/chunk.txt to lemma_meanings.txt after checking it continues the numbering."""
import os, sys
SRC = os.path.dirname(os.path.abspath(__file__))
main, chunk = os.path.join(SRC, "lemma_meanings.txt"), os.path.join(os.path.dirname(SRC), "grammar", "chunk.txt")
have = [l for l in open(main, encoding="utf8") if l.strip() and not l.startswith("#")]
last = int(have[-1].split("|")[0])
rows = [l.strip() for l in open(chunk, encoding="utf8") if l.strip()]
for k, r in enumerate(rows, last + 1):
    parts = r.split("|")
    assert len(parts) == 3 and int(parts[0]) == k and parts[1].strip() and parts[2].strip(), (k, r)
with open(main, "a", encoding="utf8", newline="\n") as f:
    f.write("\n".join(rows) + "\n")
print("added", len(rows), "-> total", last + len(rows))
