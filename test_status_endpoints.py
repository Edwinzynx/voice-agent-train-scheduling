import httpx

def test_endpoints():
    endpoints = [
        "https://cttrainsapi.confirmtkt.com/api/v1/train/runningstatus?trainNo=12012&startDay=0",
        "https://cttrainsapi.confirmtkt.com/api/v1/liveTrainStatus?trainNo=12012&startDay=0",
        "https://securedapi.confirmtkt.com/api/platform/trainrunningstatus?trainNo=12012&startDay=0",
        "https://www.confirmtkt.com/api/platform/trainrunningstatus?trainNo=12012&startDay=0",
        "https://cttrainsapi.confirmtkt.com/api/v1/trains/runningstatus?trainNo=12012&startDay=0"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.confirmtkt.com",
        "Referer": "https://www.confirmtkt.com/"
    }
    
    for url in endpoints:
        print(f"Testing URL: {url}")
        try:
            r = httpx.get(url, headers=headers, timeout=10.0)
            print(f"Status Code: {r.status_code}")
            if r.status_code == 200:
                print(f"Success! Response: {r.text[:300]}")
            else:
                print(f"Failed. Response snippet: {r.text[:150]}")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_endpoints()
