import requests
import json

def test_api():
    base_url = "http://localhost:8000/api"
    
    # Test companies list
    print("=== Testing Companies List ===")
    try:
        response = requests.get(f"{base_url}/companies/")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Companies found: {len(data.get('companies', []))}")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test current company
    print("\n=== Testing Current Company ===")
    try:
        response = requests.get(f"{base_url}/companies/current")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test company stats
    print("\n=== Testing Company Stats ===")
    try:
        response = requests.get(f"{base_url}/companies/1bf9b50e/stats")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_api()