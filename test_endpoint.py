import requests
import sys

url = "http://localhost:8000/inventory-audits/skip"
try:
    response = requests.post(url)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
