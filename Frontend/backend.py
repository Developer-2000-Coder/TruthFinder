from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json, re, os, datetime
from rank_bm25 import BM25Okapi
from difflib import SequenceMatcher
import uvicorn

app = FastAPI(title="TruthFinder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "data.json"
if not os.path.exists(DATA_FILE):
    raise RuntimeError(f"{DATA_FILE} not found in working directory. Put your dataset there.")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

def normalize_item(it):
    return {
        "title": it.get("title", ""),
        "content": it.get("content", "") or it.get("summary","") or "",
        "summary": it.get("summary",""),
        "source": it.get("source",""),
        "url": it.get("url",""),
        "published_date": it.get("published_date",""),
        "credibility_score": float(it.get("credibility_score", 0) or 0)
    }

data = [normalize_item(it) for it in raw_data]

CREDIBILITY_MAP = {
    "bbc": 0.9,
    "cnn": 0.7,
    "nytimes": 0.7,
    "reuters": 0.8,
    "sky": 0.7,
    "dw": 0.7,
    "timesofindia": 0.7,
    "rt": 0.4
}

for item in data:
    if item["credibility_score"] == 0:
        src = item.get("source","").lower()
        for key, score in CREDIBILITY_MAP.items():
            if key in src:
                item["credibility_score"] = score
                break
        else:
            item["credibility_score"] = 0.7

def clean_text(t: str):
    if not t:
        return ""
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", s).strip().lower()

corpus_tokens = [ (clean_text(f"{it['title']} {it['content']} {it.get('summary','')}")).split() for it in data ]
bm25 = BM25Okapi(corpus_tokens)

def parse_date(s: str):
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.datetime.strptime(s, fmt)
            except Exception:
                continue
    return None

def recency_boost(published_date_str):
    if not published_date_str:
        return 0.0
    dt = parse_date(published_date_str)
    if not dt:
        return 0.0
    days = (datetime.datetime.utcnow() - dt).days
    return max(0.0, 1.0 - (days / 365.0))

def fuzzy_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

@app.get("/search")
def search(
    q: str = Query(..., min_length=1),
    bm25_weight: float = Query(0.7, ge=0.0, le=1.0),
    sort: str = Query("final"),
    size: int = Query(50, ge=1, le=500)
):
    q_clean = clean_text(q)
    q_tokens = q_clean.split()

    bm25_scores = bm25.get_scores(q_tokens) if q_tokens else [0.0]*len(data)

    results = []
    for i, item in enumerate(data):
        rank_score = float(bm25_scores[i])

        rec_boost = recency_boost(item.get("published_date", ""))

        final_score = (rank_score * bm25_weight) + (item["credibility_score"] * (1.0 - bm25_weight)) + (0.1 * rec_boost)

        results.append({
            "title": item["title"],
            "content": item["content"],
            "summary": item.get("summary",""),
            "source": item.get("source",""),
            "url": item.get("url",""),
            "published_date": item.get("published_date",""),
            "credibility_score": item.get("credibility_score",0.0),
            "rank_score": rank_score,
            "final_score": final_score
        })

    q_lower = q.lower()
    def matches(it):
        text = " ".join([it.get("title",""), it.get("content",""), it.get("summary","")]).lower()
        if q_lower in text:
            return True
        for token in q_lower.split():
            for word in text.split():
                if word.startswith(token):
                    return True
        snippet = (it.get("title","") + " " + (it.get("content","")[:200] or "")).lower()
        if fuzzy_ratio(q_lower, snippet) > 0.45:
            return True
        return False

    filtered = [r for r in results if matches(r)]

    if sort == "bm25":
        filtered.sort(key=lambda x: x["rank_score"], reverse=True)
    elif sort == "cred":
        filtered.sort(key=lambda x: x["credibility_score"], reverse=True)
    elif sort == "date":
        def key_date(x):
            dt = parse_date(x.get("published_date",""))
            return (dt.timestamp() if dt else 0)
        filtered.sort(key=key_date, reverse=True)
    else:
        filtered.sort(key=lambda x: x["final_score"], reverse=True)

    out = filtered[:size]
    return {"count": len(filtered), "results": out}

@app.post("/search")
def search_post(payload: dict):
    q = payload.get("q", "")
    bm25_weight = float(payload.get("bm25_weight", 0.7))
    sort = payload.get("sort", "final")
    size = int(payload.get("size", 50))
    return search(q=q, bm25_weight=bm25_weight, sort=sort, size=size)

if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
