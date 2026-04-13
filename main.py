import logging
import os
from time import sleep

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

HOST = os.getenv("HOST")
API_KEY = os.getenv("API_KEY")
SITE_ID = os.getenv("SITE_ID")

BASE_URL = f"https://{HOST}/proxy/network/integration/v1"


# https://antonz.org/is-online/
INTERNET_CHECKS = [
    "https://google.com/generate_204",
    "http://cp.cloudflare.com/generate_204",
    "http://connectivity-check.ubuntu.com",
    "http://connect.rom.miui.com/generate_204",
    "http://spectrum.s3.amazonaws.com/kindle-wifi/wifistub.html",
    "http://captive.apple.com/hotspot-detect.html",
    "http://network-test.debian.org/nm",
    "http://nmcheck.gnome.org/check_network_status.txt",
    "http://detectportal.firefox.com/success.txt",
]


def main():
    while True:
        failed_count = 0
        while True:
            internet_available = get_is_internet_available()
            if not internet_available:
                failed_count += 1
                logging.warning("Internet connection test failed")
            else:
                failed_count = 0
                logging.debug("Internet connection test successful")
            if failed_count >= 5:
                break
            if failed_count > 0:
                sleep(15)
            else:
                sleep(60*5)

        logging.error("Internet connection lost")

        restart_udm()

        sleep(60*10)


def check_http(url: str, timeout: int = 3) -> bool:
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code < 400
    except Exception:
        return False

def get_is_internet_available() -> bool:
    for internet_check in INTERNET_CHECKS:
        if check_http(internet_check):
            return True
    return False

def unifi_request(endpoint, method="GET", json=None):
    url = BASE_URL + endpoint
    result = requests.request(method, url, headers={"Accept": "application/json", "X-API-KEY": API_KEY}, json=json, verify=False)
    result.raise_for_status()
    return result

def restart_udm():
    endpoint = f"/sites/{SITE_ID}/devices?limit=1"
    get_result = unifi_request(endpoint)
    device_id = get_result.json()['data'][0]['id']
    restart_request = {"action": "RESTART"}
    unifi_request(f"/sites/{SITE_ID}/devices/{device_id}/actions", method="POST", json=restart_request)



if __name__ == '__main__':
    main()