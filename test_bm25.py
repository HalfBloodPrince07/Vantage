import requests
import urllib3
urllib3.disable_warnings()

query = "Show me the resume of Vishakha"

# Test the EXACT BM25 query used in hybrid_search
bm25_query = {
    "size": 50,
    "query": {
        "bool": {
            "should": [
                {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "detailed_summary^3",
                            "full_content^2",
                            "filename^2",
                            "keywords^4"
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                {
                    "match_phrase": {
                        "detailed_summary": {
                            "query": query,
                            "boost": 2
                        }
                    }
                }
            ],
            "minimum_should_match": 1
        }
    }
}

print(f"Testing BM25 query from hybrid_search for: '{query}'")
print("="*60)

r = requests.post(
    'https://localhost:9200/locallens_index/_search', 
    auth=('admin', 'LocalLens@1234'), 
    verify=False, 
    json=bm25_query
)

data = r.json()
hits = data.get('hits', {}).get('hits', [])

print(f"BM25 Results: {len(hits)} documents")
print("-"*60)

for i, h in enumerate(hits[:10], 1):
    filename = h['_source'].get('filename', '?')
    score = h.get('_score', 0)
    print(f"{i}. [{score:.2f}] {filename}")
    if 'vishakha' in filename.lower():
        print("    ^^^ VISHAKHA FOUND IN BM25 ^^^")

print("="*60)

# Now check if Vishakha doc has content_summary or detailed_summary
print("\nChecking Vishakha document fields...")
r2 = requests.get(
    'https://localhost:9200/locallens_index/_search', 
    auth=('admin', 'LocalLens@1234'), 
    verify=False, 
    json={
        'query': {'wildcard': {'filename': '*ishakha*'}},
        'size': 1,
        '_source': ['filename', 'detailed_summary', 'keywords', 'full_content']
    }
)
data2 = r2.json()
hits2 = data2.get('hits', {}).get('hits', [])
if hits2:
    src = hits2[0]['_source']
    print(f"Filename: {src.get('filename')}")
    print(f"detailed_summary exists: {'detailed_summary' in src}")
    print(f"detailed_summary length: {len(src.get('detailed_summary', ''))}")
    print(f"detailed_summary preview: {src.get('detailed_summary', '')[:300]}...")
    print(f"keywords: {src.get('keywords', '')[:200]}")
else:
    print("Vishakha doc not found in wildcard search!")
