from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
API_KEY = os.getenv("NCBI_API_KEY")  # 任意

@app.get("/")
def root():
    return jsonify({"status": "ok", "service": "pubmed-mcp"}), 200

@app.get("/healthz")
def healthz():
    return "ok", 200

@app.get("/search")
def search():
    q = request.args.get("q")
    retmax = int(request.args.get("n", 5))
    if not q:
        return jsonify({"error": "missing q"}), 400
    params = {"db": "pubmed", "term": q, "retmode": "json", "retmax": retmax}
    if API_KEY: params["api_key"] = API_KEY
    r = requests.get(EUTILS + "esearch.fcgi", params=params, timeout=20)
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return jsonify({"hits": []})
    fetch = requests.get(
        EUTILS + "esummary.fcgi",
        params={"db": "pubmed", "id": ",".join(ids), "retmode": "json", **({"api_key": API_KEY} if API_KEY else {})},
        timeout=20
    ).json()
    out = []
    for pmid in ids:
        itm = fetch.get("result", {}).get(pmid, {})
        out.append({
            "pmid": pmid,
            "title": itm.get("title"),
            "journal": itm.get("fulljournalname"),
            "pubdate": itm.get("pubdate"),
            "authors": [a.get("name") for a in itm.get("authors", [])][:10],
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        })
    return jsonify({"hits": out})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
