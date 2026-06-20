import httpx
import json

def test_api():
    url = "https://cttrainsapi.confirmtkt.com/api/v1/trains/search"
    params = {
        "sourceStationCode": "NDLS",
        "destinationStationCode": "CDG",
        "dateOfJourney": "20-06-2026"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.confirmtkt.com",
        "Referer": "https://www.confirmtkt.com/"
    }
    
    print(f"Calling: {url} with params {params}")
    try:
        r = httpx.get(url, params=params, headers=headers, timeout=10.0)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            # print top-level keys
            print("Response keys:", list(data.keys()))
            
            # Print details about data
            actual_data = data.get("data", {})
            print("Data keys:", list(actual_data.keys()) if isinstance(actual_data, dict) else type(actual_data))
            
            if isinstance(actual_data, dict):
                trains = actual_data.get("trainList", [])
                print(f"Found {len(trains)} trains in trainList!")
                if trains:
                    print("\nFirst train info:")
                    print(json.dumps(trains[0], indent=2))
                else:
                    print("trainList is empty. Printing first 1000 characters of data:")
                    print(json.dumps(actual_data, indent=2)[:1000])
            else:
                print("data is not a dictionary. Sample:", str(actual_data)[:500])
        else:
            print("Response:", r.text[:500])
    except Exception as e:
        print("Error:", e)

def test_station_resolution():
    url = "https://cttrainsapi.confirmtkt.com/api/v2/trains/stations/auto-suggestion"
    params = {
        "searchString": "patiala",
        "popularStnListLimit": "5",
        "preferredStnListLimit": "5",
        "channel": "mwebd",
        "language": "EN"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.confirmtkt.com",
        "Referer": "https://www.confirmtkt.com/"
    }
    
    print(f"Calling: {url} with params {params}")
    try:
        r = httpx.get(url, params=params, headers=headers, timeout=10.0)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print("Response keys:", list(data.keys()) if isinstance(data, dict) else type(data))
            if isinstance(data, list):
                print(f"Found {len(data)} suggestions. First 3 suggestions:")
                for item in data[:3]:
                    print(f"  Name: {item.get('name')}, Code: {item.get('code')}")
            elif isinstance(data, dict):
                print("Response data:", json.dumps(data, indent=2)[:500])
        else:
            print("Response:", r.text[:500])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    # test_api()
    test_station_resolution()
