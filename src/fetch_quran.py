import json, re, sys, urllib.request, concurrent.futures as cf, os
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
B = "https://api.quran.com/api/v4"
TR = {20:"en", 45:"ru", 113:"kk"}
def get(u):
    err=None
    for i in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"hifz-builder"}), timeout=60) as r:
                return json.load(r)
        except Exception as e: err = e
    raise err
en = get(B+"/chapters?language=en")["chapters"]; ru = get(B+"/chapters?language=ru")["chapters"]
index = [{"id":c["id"],"n":c["name_simple"],"a":c["name_arabic"],"en":c["translated_name"]["name"],"ru":r["translated_name"]["name"],
          "c":c["verses_count"],"p":c["revelation_place"],"b":c["bismillah_pre"]} for c,r in zip(en,ru)]
json.dump(index, open(os.path.join(out,"chapters.json"),"w",encoding="utf8"), ensure_ascii=False, separators=(",",":"))
def raw(c):
    vs, page = [], 1
    while True:
        d = get(f"{B}/verses/by_chapter/{c['id']}?words=true&word_fields=text_qpc_hafs,text_uthmani&fields=text_qpc_hafs&translations=20,45,113&audio=7&per_page=50&page={page}")
        vs += d["verses"]
        if not d["pagination"]["next_page"]: break
        page += 1
    json.dump(vs, open(os.path.join(out,f"raw{c['id']}.json"),"w",encoding="utf8"), ensure_ascii=False)
    return c["id"], len(vs)
with cf.ThreadPoolExecutor(8) as ex:
    res = list(ex.map(raw, en))
print(sum(n for _,n in res))
