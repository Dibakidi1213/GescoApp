#!/usr/bin/env python
"""Test IGE API endpoint"""

from app import app, db
from models import BulletinConfig, Section, School
import json

def test_api_endpoint():
    """Test if API returns IGE number"""
    print("=" * 60)
    print("🧪 TESTING API ENDPOINT")
    print("=" * 60)
    
    with app.test_client() as client:
        # Test getting config for SCIENCES level 1 from school 1
        # Correct endpoint: /api/bulletin-config/<section_ref>/<level>
        response = client.get('/admin/api/bulletin-config/SCIENCES/1?school_id=1')
        
        print(f"\nAPI Request: /admin/api/bulletin-config/SCIENCES/1?school_id=1")
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse JSON:")
        
        if response.status_code == 200:
            data = response.get_json()
            print(json.dumps(data, indent=2))
            
            if 'ige_number' in data:
                print(f"\n✅ IGE Number in API response: {data.get('ige_number')}")
            else:
                print(f"\n❌ IGE Number NOT in API response!")
                print(f"Available fields: {list(data.keys()) if data else 'No data'}")
        else:
            print(f"❌ API Error ({response.status_code}): {response.text[:200]}")

if __name__ == '__main__':
    test_api_endpoint()
