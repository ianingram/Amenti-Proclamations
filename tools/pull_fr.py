"""Pull every presidential proclamation published in the Federal Register (1994 on).

Writes data/p/<number>.json (one per proclamation) and the indexes data/index.json
and data/presidents.json. Existing files are kept, so a re-run only fetches new ones.
Source: the Federal Register API (federalregister.gov), an official U.S. government source.
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request, datetime

API = "https://www.federalregister.gov/api/v1/documents.json"
UA = {"User-Agent": "Amenti-Proclamations archive (github.com/IanIngram/Amenti-Proclamations)"}
FIELDS = ["document_number", "proclamation_number", "title", "signing_date", "publication_date",
          "president", "raw_text_url", "html_url", "pdf_url", "citation", "disposition_notes"]
OUT = "data/p"

def get(url, tries=4):
    for k in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception as e:
            if k == tries - 1: raise
            time.sleep(3 * (k + 1))

def listing(year):
    out, page = [], 1
    while True:
        q = [("conditions[type][]", "PRESDOCU"), ("conditions[presidential_document_type][]", "proclamation"),
             ("conditions[publication_date][year]", str(year)), ("per_page", "1000"), ("page", str(page)), ("order", "oldest")]
        q += [("fields[]", f) for f in FIELDS]
        d = json.loads(get(API + "?" + urllib.parse.urlencode(q)))
        out += d.get("results") or []
        if page >= (d.get("total_pages") or 1): return out
        page += 1

def clean(raw, number):
    t = html.unescape(re.sub(r"<[^>]+>", "", raw.decode("utf-8", "replace"))).replace("\r", "")
    m = re.search(r"Proclamation\s+%s\b" % re.escape(str(number)), t)
    if m: t = t[m.start():]
    t = re.split(r"\n\s*\[FR Doc\.?|\n\s*Billing code", t)[0]
    # drop Federal Register furniture
    t = re.sub(r"\[\[Page[^\]]*\]\]", "", t)
    t = re.sub(r"\n\s*Presidential Documents\s*\n", "\n", t)
    t = re.sub(r"\n\s*Federal Register\s*\nVol\.[^\n]*\n[^\n]*\n", "\n", t)
    t = re.sub(r"\n\s*_{5,}\s*\n", "\n\n", t)
    t = re.sub(r"\n\s*Title 3--\s*\n\s*The President\s*\n", "\n\n", t)
    paras = []
    for block in re.split(r"\n\s*\n", t):
        line = re.sub(r"\s+", " ", block).strip()
        if line: paras.append(line)
    return paras

def main():
    os.makedirs(OUT, exist_ok=True)
    years = range(int(sys.argv[1]) if len(sys.argv) > 1 else 1994, datetime.date.today().year + 1)
    new = 0
    for y in years:
        rows = listing(y)
        print(y, len(rows), flush=True)
        for r in rows:
            n = r.get("proclamation_number") or ("fr-" + r["document_number"])
            path = f"{OUT}/{n}.json"
            if os.path.exists(path): continue
            try:
                paras = clean(get(r["raw_text_url"]), n) if r.get("raw_text_url") else []
            except Exception as e:
                print("  text failed", n, e); paras = []
            rec = {"number": n, "title": r.get("title"), "signed": r.get("signing_date"),
                   "published": r.get("publication_date"),
                   "president": (r.get("president") or {}).get("name"),
                   "president_id": (r.get("president") or {}).get("identifier"),
                   "citation": r.get("citation"), "fr_document": r.get("document_number"),
                   "source": r.get("html_url"), "pdf": r.get("pdf_url"), "text_source": r.get("raw_text_url"),
                   "notes": r.get("disposition_notes"), "verified": False, "paragraphs": paras}
            json.dump(rec, open(path, "w"), ensure_ascii=False, indent=1)
            new += 1; time.sleep(0.15)
    build_indexes(); print("new", new)

def build_indexes():
    recs = [json.load(open(f"{OUT}/{f}")) for f in os.listdir(OUT) if f.endswith(".json")]
    recs.sort(key=lambda r: (r["signed"] or r["published"] or "", str(r["number"])))
    idx = [{k: r[k] for k in ("number", "title", "signed", "president_id")} for r in recs]
    json.dump(idx, open("data/index.json", "w"), ensure_ascii=False, separators=(",", ":"))
    pres = {}
    for r in recs:
        p = pres.setdefault(r["president_id"], {"id": r["president_id"], "name": r["president"], "count": 0, "first": r["signed"], "last": r["signed"]})
        p["count"] += 1; p["last"] = r["signed"]
    json.dump(sorted(pres.values(), key=lambda p: p["first"] or ""), open("data/presidents.json", "w"), ensure_ascii=False, indent=1)
    print("index", len(idx), "presidents", len(pres))

if __name__ == "__main__":
    main()
