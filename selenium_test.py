from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_selenium():
    print("Setting up Chrome options...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headlessly
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    print("Installing Chrome driver...")
    service = Service(ChromeDriverManager().install())
    
    print("Launching driver...")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.confirmtkt.com/"
        print(f"Navigating to {url}...")
        driver.get(url)
        time.sleep(3) # Wait for page load
        
        print("Page title:", driver.title)
        print("Current URL:", driver.current_url)
        
        # Take a screenshot to verify visual rendering
        driver.save_screenshot("confirmtkt_screenshot.png")
        print("Screenshot saved successfully!")
    except Exception as e:
        print(f"Error during Selenium execution: {e}")
    finally:
        print("Quitting driver...")
        driver.quit()

if __name__ == "__main__":
    test_selenium()
