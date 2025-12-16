import requests
import urllib3
urllib3.disable_warnings()

# Test direct BM25 search for "Vishakha"
print("Testing BM25 search for 'Vishakha'...")
r = requests.get(
    'https://localhost:9200/locallens_index/_search', 
    auth=('admin', 'LocalLens@1234'), 
    verify=False, 
    json={
        'query': {
            'multi_match': {
                'query': 'Vishakha resume',
                'fields': ['filename^3', 'content_summary^2', 'keywords', 'full_content'],
                'type': 'best_fields'
            }
        },
        'size': 10,
        '_source': ['filename', 'content_summary']
    }
)

data = r.json()
hits = data.get('hits', {}).get('hits', [])

print(f"BM25 Results: {len(hits)} documents")
print("="*60)

for i, h in enumerate(hits, 1):
    filename = h['_source'].get('filename', '?')
    score = h.get('_score', 0)
    summary = h['_source'].get('content_summary', '')[:150]
    print(f"{i}. [{score:.2f}] {filename}")
    print(f"   Summary: {summary}...")
    print()

if not hits:
    print("❌ NO RESULTS! BM25 search is not finding Vishakha.")
    print("\nChecking document content for 'Vishakha'...")
    
    # Check if the content contains Vishakha
    r2 = requests.get(
        'https://localhost:9200/locallens_index/_search', 
        auth=('admin', 'LocalLens@1234'), 
        verify=False, 
        json={
            'query': {
                'wildcard': {'filename': '*ishakha*'}
            },
            'size': 5,
            '_source': ['filename', 'content_summary', 'keywords']
        }
    )
    data2 = r2.json()
    hits2 = data2.get('hits', {}).get('hits', [])
    print(f"Wildcard search found: {len(hits2)} docs")
    for h in hits2:
        print(f"  - {h['_source'].get('filename')}")
        print(f"    Summary: {h['_source'].get('content_summary', '')[:200]}")
        print(f"    Keywords: {h['_source'].get('keywords', '')[:100]}")
