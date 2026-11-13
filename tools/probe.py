# Print what the Federal Register API returns for presidential proclamations.
import json, urllib.request, urllib.parse
B = "https://www.federalregister.gov/api/v1/documents.json"
q = [("conditions[type][]", "PRESDOCU"), ("conditions[presidential_document_type][]", "proclamation"),
     ("per_page", "2"), ("order", "oldest")]
for f in ["document_number","proclamation_number","title","signing_date","publication_date","president",
          "raw_text_url","body_html_url","html_url","pdf_url","citation","executive_order_number","disposition_notes"]:
    q.append(("fields[]", f))
u = B + "?" + urllib.parse.urlencode(q)
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Amenti-Proclamations (archive build)"})))
print("count", d.get("count"), "pages", d.get("total_pages"))
print(json.dumps(d.get("results"), indent=1)[:4000])
r = d["results"][0]
t = urllib.request.urlopen(r["raw_text_url"]).read().decode("utf-8", "replace")
print("---- raw text sample ----"); print(t[:1500])
