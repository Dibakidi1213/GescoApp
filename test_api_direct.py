from app import app
from models import Section, db

with app.app_context():
    # Test l'endpoint /api/bulletin-levels avec authentification
    client = app.test_client()
    
    sections_to_test = ['LATIN PHILO', 'SCIENCES']
    
    for section_name in sections_to_test:
        print(f"\n=== Test GET /admin/api/bulletin-levels/{section_name} ===")
        
        # Encoder proprement l'URL
        url = f'/admin/api/bulletin-levels/{section_name}?school_id=1'
        print(f"URL: {url}")
        
        response = client.get(url, follow_redirects=False)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.content_type}")
        print(f"Location (if redirect): {response.headers.get('Location', 'N/A')}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"Data: {data}")
        else:
            print(f"Response: {response.data[:200]}")
