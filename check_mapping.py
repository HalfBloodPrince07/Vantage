import requests
import urllib3
urllib3.disable_warnings()

# Check actual field names in the index
print("Checking actual field names in indexed documents...")
r = requests.get(
    'https://localhost:9200/locallens_index/_mapping', 
    auth=('admin', 'LocalLens@1234'), 
    verify=False
)
data = r.json()

# Get properties
props = data.get('locallens_index', {}).get('mappings', {}).get('properties', {})
print("\nIndexed fields:")
for field_name in sorted(props.keys()):
    field_type = props[field_name].get('type', 'unknown')
    print(f"  - {field_name}: {field_type}")
