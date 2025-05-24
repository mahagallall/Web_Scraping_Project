import requests
from requests.structures import CaseInsensitiveDict
import json
import time
import logging
import colorlog
import schedule

# Configure colorlog
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s:%(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

logger = colorlog.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def fetch_version_json():
    """Fetch version.json from the specified URL."""
    url = "https://raw.githubusercontent.com/mahagallall/Web_Scraping_Project/refs/heads/main/version.json"
    try:
        response = requests.get(url)
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch version.json: {e}")
        return None

def check_api_key(api_key):
    """Check if the given Serper API key is expired based on 'Not enough credits' message."""
    url = "https://google.serper.dev/search"
    headers = CaseInsensitiveDict()
    headers["X-API-KEY"] = api_key

    try:
        response = requests.get(url, headers=headers)
        response_text = response.text
        #print("LOG",response_text)
        logger.debug(f"Response for API Key {api_key[:8]}...: Status {response.status_code}, Content: {response_text}")
        
        if "Not enough credits" in response_text:
            logger.warning(f"API Key {api_key[:8]}... is expired (Not enough credits)")
            return False
        else:
            logger.info(f"API Key {api_key[:8]}... is valid")
            return True
    except requests.RequestException as e:
        logger.error(f"Request failed for API Key {api_key[:8]}...: {e}")
        return False

def check_all_api_keys():
    """Check all Serper API keys from version.json."""
    logger.info("Starting API key check...")
    version_data = fetch_version_json()
    
    if not version_data or "settings" not in version_data or "serper_api_keys" not in version_data["settings"]:
        logger.error("Invalid or missing serper_api_keys in version.json")
        return

    api_keys = version_data["settings"]["serper_api_keys"]
    valid_keys = []
    expired_keys = []

    for api_key in api_keys:
        if check_api_key(api_key):
            valid_keys.append(api_key)
        else:
            expired_keys.append(api_key)

    logger.info(f"Check complete. Valid keys: {len(valid_keys)}, Expired keys: {len(expired_keys)}")
    if valid_keys:
        logger.info(f"Valid API Keys: {[key[:8] + '...' for key in valid_keys]}")
    if expired_keys:
        logger.warning(f"Expired API Keys: {[key[:8] + '...' for key in expired_keys]}")

def main():
    """Main function to schedule and run API key checks."""
    logger.info("Starting Serper API Key Checker")
    
    # Schedule the check every 12 hours
    schedule.every(12).hours.do(check_all_api_keys)
    
    # Run the first check immediately
    check_all_api_keys()
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute for pending tasks

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Serper API Key Checker stopped by user")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
