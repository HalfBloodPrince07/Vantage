"""
Debug script to check OpenSearch indexed documents
Run this from the LocaLense_V2 directory
"""

import asyncio
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    from backend.config import load_config
    from backend.opensearch_client import OpenSearchClient
    
    config = load_config()
    client = OpenSearchClient(config)
    
    print("\n" + "="*60)
    print("OpenSearch Document Checker")
    print("="*60)
    
    # Get index stats
    try:
        stats = await client.get_stats()
        print(f"\n📊 Index Stats: {stats}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
    
    # List all documents
    try:
        query = {
            "query": {"match_all": {}},
            "size": 100,
            "_source": ["filename", "file_path", "content_summary", "file_type", "keywords"]
        }
        
        response = await client.client.search(
            index=client.index_name,
            body=query
        )
        
        hits = response.get('hits', {}).get('hits', [])
        print(f"\n📄 Total indexed documents: {len(hits)}")
        print("-"*60)
        
        vishakha_found = False
        for idx, hit in enumerate(hits, 1):
            source = hit.get('_source', {})
            filename = source.get('filename', 'Unknown')
            file_type = source.get('file_type', 'Unknown')
            summary = source.get('content_summary', '')[:100]
            
            # Check if this is Vishakha
            if 'vishakha' in filename.lower() or 'vishakha' in summary.lower():
                vishakha_found = True
                print(f"\n✅ FOUND VISHAKHA!")
                print(f"   ID: {hit.get('_id')}")
                print(f"   Filename: {filename}")
                print(f"   Summary: {summary}...")
                print(f"   Keywords: {source.get('keywords', '')[:100]}")
            
            print(f"{idx}. [{file_type:8}] {filename}")
        
        if not vishakha_found:
            print("\n❌ Vishakha document NOT FOUND in index!")
            print("   This means the document was either not indexed or failed during indexing.")
        
    except Exception as e:
        print(f"❌ Error listing documents: {e}")
        import traceback
        traceback.print_exc()
    
    await client.close()
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
