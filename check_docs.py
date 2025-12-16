import requests
import urllib3
urllib3.disable_warnings()

r = requests.get(
    'https://localhost:9200/locallens_index/_search', 
    auth=('admin', 'LocalLens@1234'), 
    verify=False, 
    json={'query': {'match_all': {}}, 'size': 50, '_source': ['filename', 'content_summary']}
)

data = r.json()
hits = data.get('hits', {}).get('hits', [])

print(f"Total indexed documents: {len(hits)}")
print("="*60)

vishakha_found = False
for i, h in enumerate(hits, 1):
    filename = h['_source'].get('filename', '?')
    summary = h['_source'].get('content_summary', '')[:80]
    print(f"{i:2}. {filename}")
    
    if 'vishakha' in filename.lower() or 'vishakha' in summary.lower():
        vishakha_found = True
        print(f"    ^^^ VISHAKHA FOUND ^^^")

print("="*60)
if vishakha_found:
    print("✅ Vishakha document IS indexed")
else:
    print("❌ Vishakha document NOT indexed - check if file was processed")
